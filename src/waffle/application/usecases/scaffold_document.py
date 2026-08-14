"""scaffold document — document.json の骨格生成（create）と値書き込み（fill）。

Harness 原則: AI は「値」だけを生成し、document.json の構造は engine が組む。
- create: schema を機械走査して skeleton（自分の schema で valid・status=enum 先頭）と
  fillTemplate（値フィールドの path × x-prompt-write）を生成し、x-source-target に書く。
- fill: AI が生成した values を、宣言済み値フィールドにのみ機械的に書き込む（構造保護）。
  値の型/enum 適合検証は uc-validate-document の責務（疎結合）。
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_document, load_schema, require_schema_ref
from waffle.domain.services import path_template
from waffle.domain.services.fill_template import build_const_paths as _build_const_paths
from waffle.domain.services.fill_template import resolve_ref as _resolve_ref
from waffle.domain.services.fill_template import build_fill_template as _build_fill_template
from waffle.domain.services.fill_template import build_skeleton as _build_skeleton
from waffle.domain.services.fill_template import build_top_level_const_paths as _build_top_level_const_paths
from waffle.domain.services.schema_versioning import has_version, latest_version, version_number
from waffle.domain.services.fill_template import build_top_level_fill_template as _build_top_level_fill_template
from waffle.domain.services.fill_template import content_def as _content_def
from waffle.domain.services.fill_template import discriminator_candidates as _discriminator_candidates
from waffle.domain.services.schema_discriminator import discriminator_key as _discriminator_key
from waffle.shared.result import Err, Ok, Result

def _err(code: str, message: str) -> Err:
    return Err(message, [code])

class ScaffoldDocument:
    """documentの骨格を作り、宣言された欄へ値を書き込む。"""
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, operation: str, params: dict | None = None) -> Result[dict]:
        """documentの骨格を作り、宣言された欄へ値を書き込む。

        Args:
            operation: 行う操作の種類。
            params: その操作に固有の引数。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        params = params or {}
        if operation == "create":
            return self._create(params)
        if operation == "fill":
            return self._fill(params)
        if operation == "clear_field":
            return self._clear_field(params)
        if operation == "migrate_schema":
            return self._migrate_schema(params)
        return _err("INVALID_OPERATION", f"未知の operation: {operation}")

    def _latest_ref(self, schema_ref: str) -> Result[str]:
        """新しく作ってよい版へ解決する。

        版が書かれていなければ最新へ補い、書かれていて最新でなければ拒む。
        指示や手順に版を書かせると、schemaが1つ上がった瞬間から古い版を指す。
        版を省けるようにして初めて、その固定を消せる。

        既存documentを運ぶ migrate_schema はこの制限の対象にしない。運ぶ操作まで
        塞ぐと、移行の道そのものが無くなる。

        Args:
            schema_ref: 与えられた schemaRef（'Foo' でも 'Foo/v2' でもよい）。

        Returns:
            作ってよい版まで含んだ schemaRef を持つ Ok、または拒否を表す Err。

        Raises:
            なし。
        """
        name = schema_ref.partition("/")[0]
        latest = latest_version(self._schemas.list_versions(name))
        if latest is None:
            return Ok(schema_ref)
        if not has_version(schema_ref):
            return Ok(f"{name}/{latest}")
        if version_number(schema_ref) != version_number(latest):
            return _err(
                "OUTDATED_SCHEMA_REF",
                f"{name} の最新は {latest} です。新しい document は最新の版で作ります"
                f"（既存 document を運ぶ場合は migrate_schema を使ってください）",
            )
        return Ok(schema_ref)

    def _create(self, params: dict) -> Result[dict]:
        schema_ref = params.get("schemaRef")
        document_id = params.get("documentId")
        if not schema_ref or not document_id:
            return _err("MISSING_PARAM", "create には schemaRef, documentId が必要です")
        resolved_ref = self._latest_ref(schema_ref)
        if isinstance(resolved_ref, Err):
            return resolved_ref
        schema_ref = resolved_ref.value
        # 以降は解決後の版を正本にする。元の指定が残ると、骨格やパスの
        # 組み立てが版を欠いたままの文字列を使ってしまう
        params = {**params, "schemaRef": schema_ref}
        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = params.get("discriminator") or {}
        if disc_key:
            candidates = _discriminator_candidates(schema, disc_key)
            if disc_key not in discriminator:
                return _err("MISSING_DISCRIMINATOR", f"{disc_key} の指定が必要です（候補: {', '.join(candidates)}）")
            if discriminator[disc_key] not in candidates:
                return _err(
                    "INVALID_DISCRIMINATOR",
                    f"{disc_key}='{discriminator[disc_key]}' は不正な値です（候補: {', '.join(candidates)}）",
                )

        path_vars = {"documentId": document_id, **{k: v for k, v in params.items() if isinstance(v, str)}}
        spec_kind = discriminator.get(disc_key) if disc_key else None
        content_def = _content_def(schema, discriminator)
        skeleton = _build_skeleton(schema, document_id, disc_key, discriminator, content_def, path_vars)
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        fill_template = (
            _build_top_level_fill_template(schema, protected, spec_kind)
            + _build_fill_template(schema, content_def, spec_kind)
        )

        x_source = schema.get("x-source-target") or ""
        template = x_source.get(discriminator.get(disc_key)) if isinstance(x_source, dict) else x_source
        path = path_template.resolve(template, **path_vars) if template else ""
        if path:
            existing = self._existing_document(path)
            if existing is not None:
                # べき等性: 既にdocument.jsonがある場合は、fillで埋めた既存のvaluesを保護し
                # 骨格で上書きしない（構造は保存時に既に保証済み）。
                skeleton = existing
            else:
                self._documents.save(path, skeleton)
        return Ok({"skeleton": skeleton, "fillTemplate": fill_template, "path": path})

    def _existing_document(self, path: str) -> dict | None:
        try:
            return self._documents.load(path)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _fill(self, params: dict) -> Result[dict]:
        document_path = params.get("documentPath")
        values = params.get("values")
        if not document_path or values is None:
            return _err("MISSING_PARAM", "fill には documentPath, values が必要です")
        if not isinstance(values, dict):
            # 形の違う引数で読み込みまで進むと、書き込み時に例外が境界の外へ漏れる。
            # application 境界は結果型で成否を返す規約なので、読む前に弾く。
            return _err(
                "INVALID_PARAM",
                "values は {パス: 値} の辞書で指定してください"
                f"（受け取った形: {type(values).__name__}）",
            )
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        schema_ref_result = require_schema_ref(doc)
        if isinstance(schema_ref_result, Err):
            return schema_ref_result
        schema_ref = schema_ref_result.value

        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = {disc_key: doc.get(disc_key)} if disc_key else {}
        content_def = _content_def(schema, discriminator)
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        allowed = {e["path"] for e in _build_top_level_fill_template(schema, protected)}
        allowed |= {e["path"] for e in _build_fill_template(schema, content_def)}
        const_paths = _build_top_level_const_paths(schema, protected) | _build_const_paths(schema, content_def)

        # 指定されたパスは、書き込む前に全件分類する。skip には性質の違う2種類が
        # 混ざっており、同じ扱いにすると呼び出し側が誤りに気づけない。
        #   拒否   構造保護が正しく働いた（const・documentId・discriminator）。設計どおり
        #   不正   そんな欄は無い、または書き込み単位でない。呼び出し側の誤り
        # 不正が1件でもあれば何も書かずに返す。書ける分だけ書くと、documentが半分だけ
        # 更新された状態で残り、再実行時に何が済んでいるかを呼び出し側が判断する羽目になる。
        writable: list[tuple[str, object]] = []
        rejected: list[str] = []
        invalid: list[str] = []
        for path, value in values.items():
            # const再同期: schema版更新でconst値自体が変わった既存documentを、現行schemaの
            # 宣言値と完全一致する値でのみ書き込み許可する（任意の値への上書きは引き続き拒否）
            if path in allowed or (path in const_paths and const_paths[path] == value):
                writable.append((path, value))
            elif path in const_paths or path in protected:
                rejected.append(path)
            else:
                invalid.append(path)

        if invalid:
            return _err("INVALID_FIELD_PATH", _invalid_path_message(invalid, allowed))

        written: list[str] = []
        for path, value in writable:
            if _set_path(doc, path, value, const_paths):
                written.append(path)
            else:
                rejected.append(path)
        # 書き込みが無ければ保存しない。無変更の保存は、書き込みを見ている周辺の仕組みへ
        # 変更があったかのように見える（clear_field / migrate_schema と同じ扱いに揃える）
        if written:
            self._documents.save(document_path, doc)
        return Ok({"documentPath": document_path, "written": written, "skipped": rejected})

    def _clear_field(self, params: dict) -> Result[dict]:
        document_path = params.get("documentPath")
        field_path = params.get("fieldPath")
        if not document_path or not field_path:
            return _err("MISSING_PARAM", "clear_field には documentPath, fieldPath が必要です")
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        schema_ref_result = require_schema_ref(doc)
        if isinstance(schema_ref_result, Err):
            return schema_ref_result
        schema_ref = schema_ref_result.value

        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = _discriminator_key(schema)
        discriminator = {disc_key: doc.get(disc_key)} if disc_key else {}
        content_def = _content_def(schema, discriminator)

        if _is_required_path(schema, content_def, field_path):
            return _err("REQUIRED_FIELD", f"必須フィールドは削除できません: {field_path}")

        cleared = _clear_path(doc, field_path)
        if cleared:
            self._documents.save(document_path, doc)
        return Ok({"documentPath": document_path, "cleared": cleared})

    def _migrate_schema(self, params: dict) -> Result[dict]:
        """documentのschemaRefを、既に解決可能な別のschema版へ書き換える（冪等）。
        contentの型適合検証は行わない（migrate_schema前後どちらのタイミングでも
        scaffold fillでcontentを書き換えられ、適合判定はuc-validate-documentの責務）。"""
        document_path = params.get("documentPath")
        schema_ref = params.get("schemaRef")
        if not document_path or not schema_ref:
            return _err("MISSING_PARAM", "migrate_schema には documentPath, schemaRef が必要です")
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result

        # 落とす判断は、版が同じかどうかより先に行う。同じ版なら素通しにすると、
        # 版だけ書き換えて宣言外のブロックが残ったdocumentが、二度目の運搬でも
        # 直らないまま固定される（実際にそういうdocumentを作ってしまった）
        dropped = _blocks_the_schema_does_not_declare(doc, schema_result.value)
        holding = [name for name in dropped if _block_holds_content(doc["content"][name])]
        if holding:
            return _err(
                "MIGRATION_WOULD_DISCARD_CONTENT",
                f"{schema_ref} が宣言しないブロックに中身が残っています: {', '.join(holding)}。"
                f"運び先を決めてから運んでください（この操作は内容を捨てません）",
            )

        if not dropped and doc.get("schemaRef") == schema_ref:
            return Ok({"documentPath": document_path, "schemaRef": schema_ref,
                       "changed": False, "removed": []})

        for name in dropped:
            del doc["content"][name]
        doc["schemaRef"] = schema_ref
        self._documents.save(document_path, doc)
        return Ok({"documentPath": document_path, "schemaRef": schema_ref,
                   "changed": True, "removed": dropped})

def _blocks_the_schema_does_not_declare(doc: dict, schema: dict) -> list[str]:
    """documentが持つブロックのうち、そのschemaが宣言していないものの名前を返す。

    宣言していないブロックを残したまま版だけ書き換えると、以後どの操作からも
    触れず消せないブロックが残り、documentはどの版にも適合しなくなる。

    宣言は種別ごとに分かれるので、documentが名乗る種別の枝まで解決してから見る。
    トップレベルの宣言だけを見ると、種別ごとに足されるブロックを「宣言外」と
    取り違えるか、あるいは1つも宣言が無いと読んで何も落とさないことになる。
    """
    disc_key = _discriminator_key(schema)
    discriminator = {disc_key: doc.get(disc_key)} if disc_key else {}
    declared = _content_def(schema, discriminator).get("properties", {})
    if not declared:
        return []          # contentの中身を宣言しないschemaでは、落とす判断ができない
    return [name for name in doc.get("content", {}) if name not in declared]


# ブロックの器 ── そのブロックが何であるかを示すもので、書き手が入れた内容ではない
_BLOCK_VESSEL = ("blockType", "title")


def _block_holds_content(block) -> bool:
    """ブロックの器を除いた残りに値があるか。"""
    if not isinstance(block, dict):
        return bool(block)
    return any(_has_value(v) for k, v in block.items() if k not in _BLOCK_VESSEL)


def _has_value(value) -> bool:
    if isinstance(value, (dict, list, str)):
        return len(value) > 0
    return value is not None


# --- schema 走査ヘルパ（純ロジック・機械的） ---

def _set_path(doc: dict, path: str, value, const_paths: dict | None = None) -> bool:
    """path上の中間キーが無ければ新設しながら値を設定する（呼び出し元がpathを既に
    allowed/const_pathsで検証済みのため、ここでの新設は現行schemaが宣言する経路に限られる。
    schema版更新で新設された任意ブロックへ、旧版のまま追従していない既存Documentも書き込めるようにする）。

    中間キーを新設するときは、その階層がschemaでconstとして宣言している値も一緒に埋める。
    ブロックの種別（blockType）がこれに当たり、埋めないと値だけを持つ不完全なブロックが
    でき、書き込みは成功と報告されるのにschemaへ適合しないdocumentが残る。"""
    const_paths = const_paths or {}
    parts = path.split(".")
    cur = doc
    for i, p in enumerate(parts[:-1]):
        if not isinstance(cur, dict):
            return False
        if p not in cur:
            cur[p] = _const_defaults(const_paths, ".".join(parts[: i + 1]))
        cur = cur[p]
    if not isinstance(cur, dict):
        return False
    cur[parts[-1]] = value
    return True


def _const_defaults(const_paths: dict, prefix: str) -> dict:
    """prefixが指す階層の直下にあるconstフィールドを、宣言値のまま持つdictを作る。"""
    depth = prefix.count(".") + 1
    return {
        p.split(".")[-1]: v
        for p, v in const_paths.items()
        if p.startswith(prefix + ".") and p.count(".") == depth
    }


def _invalid_path_message(invalid: list[str], allowed: set) -> str:
    """書けなかったパスごとに、何が問題で、代わりにどこを指せばよいかを述べる。

    書き込み単位より粗い指定（ブロックそのものを指す等）は、単に「知らない欄」として
    返すと呼び出し側が綴りを疑い始める。実際には正しい欄の一段上を指しているだけなので、
    その下にある書き込み単位を候補として並べる。"""
    lines = []
    for path in sorted(invalid):
        children = sorted(p for p in allowed if p.startswith(path + "."))
        if children:
            lines.append(f"{path} は書き込み単位ではありません。"
                         f"{' / '.join(children)} のいずれかを指定してください")
        else:
            lines.append(f"{path} は schema が宣言していない欄です")
    return "／".join(lines)

def _is_required_path(schema: dict, content_def: dict, path: str) -> bool:
    """pathが指す欄そのものが、それを持つ定義のrequired配列に含まれるか判定する。

    必須かどうかは欄そのもので決まる。入れ物が必須であることを中身が必須である
    ことと取り違えると、必須ブロックの中の欄が1つも消せなくなる（実際にそうなって
    いた）。よってpathの手前を辿り、最後の要素の親の宣言を見る。
    """
    parts = path.split(".")
    if parts[0] != "content" or len(parts) < 2:
        return parts[0] in schema.get("required", [])

    node = content_def
    for part in parts[1:-1]:
        node = node.get("properties", {}).get(part, {})
        if "$ref" in node:
            node = _resolve_ref(schema, node["$ref"])
        if not isinstance(node, dict):
            return False
    return parts[-1] in node.get("required", [])

def _clear_path(doc: dict, path: str) -> bool:
    """path上のキーが実在すれば削除する（冪等：存在しなければ何もせずFalseを返す）。"""
    parts = path.split(".")
    cur = doc
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    if not isinstance(cur, dict) or parts[-1] not in cur:
        return False
    del cur[parts[-1]]
    return True

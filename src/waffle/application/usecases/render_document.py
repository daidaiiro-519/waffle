"""render document — document.json を成果物（SKILL.md 等の MD 正本）にレンダリングし、
x-render-target.path の場所へ deploy する application use case。
CSS付きHTMLでの閲覧は uc-render-document-viewer が別usecaseとして担う（CQRS原則、
MD正本＝コマンド実行モデル、HTML＝読み取り専用の投影として責務を分離する）。

汎用エンジン（schema 固有ロジックを持たない）:
- frontmatter は schema の x-frontmatter から生成
- body は content の各ブロックを x-render-order でソートし、
  「見出し(x-render-level + block.title) + x-render(宣言的部品) 本体」を生成
  （部品の描画は domain/services/part_renderer に委譲）
- 出力先は x-render-target.path
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_document, load_schema, require_schema_ref
from waffle.domain.services import path_template
from waffle.domain.services.lifecycle_guard import next_status
from waffle.domain.services.part_renderer import MalformedContentError
from waffle.domain.services.part_renderer import render_body as _render_body_service
from waffle.domain.services.schema_discriminator import discriminator_key
from waffle.shared.result import Err, Ok, Result

def _err(code: str, message: str) -> Err:
    return Err(message, [code])

def _select_template(value, spec_kind: str | None) -> str:
    """x-render-target の path は、フラットな文字列（旧来）か
    specKind ごとの辞書（ネスト構造）のどちらでも書ける。辞書なら該当 specKind を選ぶ。"""
    if isinstance(value, dict):
        return value.get(spec_kind, "") if spec_kind else ""
    return value or ""

def _select_deploy(value, spec_kind: str | None) -> list:
    """x-render-target の deploy は、フラットな配列（旧来）か
    specKind ごとの辞書（discriminatorで出し分け）のどちらでも書ける。辞書なら該当 specKind を選ぶ。"""
    if isinstance(value, dict):
        return value.get(spec_kind, []) if spec_kind else []
    return value or []

def _select_field_map(value: dict, spec_kind: str | None) -> dict:
    """x-render-target.pathVars・x-frontmatter は、フラットな辞書（フィールド名→ドットパス。
    discriminator非依存）か discriminatorごとの辞書（kind→{フィールド名→ドットパス}）の
    どちらでも書ける。値が全て dict なら discriminatorごとの宣言とみなし、該当 kind を選ぶ
    （discriminatorの分岐で content の形が変わり、参照できるドットパスも変わるため）。"""
    if value and all(isinstance(v, dict) for v in value.values()):
        return value.get(spec_kind, {}) if spec_kind else {}
    return value

class RenderDocument:
    def __init__(
        self,
        documents: DocumentRepository,
        schemas: SchemaRepository,
    ) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, document_path: str, deploy: bool = True) -> Result[dict]:
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

        # render は schema 適合検証をしない（検証は uc-validate-document の責務・疎結合）。
        # 不正な構造の document は best-effort で描画される（Orchestrator が事前 validate する前提）。
        # ただし status 遷移の可否だけは schema の x-lifecycle（宣言的）を読む薄い guard で守る。
        # schema がこの document 種別で "render" を状態遷移コマンドと定義していない場合
        # （例: SkillSchema/AgentSchema には無い）、status は問わない。
        lifecycle = schema.get("x-lifecycle")
        defines_render = lifecycle is not None and any(
            t["command"] == "render" for t in lifecycle["transitions"]
        )
        if defines_render and next_status(schema, doc.get("status"), "render") is None:
            return _err(
                "INVALID_TRANSITION",
                f"status '{doc.get('status')}' からrenderへは遷移できません",
            )

        target = schema.get("x-render-target") or {}
        if not target.get("path"):
            return _err(
                "NO_RENDER_TARGET",
                f"{schema_ref} は x-render-target.path を宣言していません。"
                "専用の成果物確定コマンドを使ってください（例: HandoffSchemaは render-handoff-template）。",
            )
        formats = target.get("formats") or ["md"]
        fmt = formats[0]  # MD 正本（HTML は uc-render-document-viewer が別usecaseとして担う）
        defs = schema.get("$defs", {})

        spec_kind = doc.get(discriminator_key(schema))
        try:
            output = self._render_frontmatter(doc, schema, spec_kind) + self._render_body(doc, defs)
        except MalformedContentError as e:
            return _err("MALFORMED_CONTENT", str(e))

        path_vars = self._resolve_path_vars(doc, schema, document_path, spec_kind)
        path_template_str = _select_template(target.get("path"), spec_kind)

        canonical = path_template.resolve(path_template_str, **path_vars) if path_template_str else ""
        deployed: list[str] = []
        if deploy and canonical:
            try:
                # canonical（.waffle 配下）に書く
                self._documents.write_text(canonical, output)
                tool_targets = self._resolve_tool_deploy_targets(doc.get("documentType"), path_vars, spec_kind)
                if tool_targets is not None:
                    # .waffle/config.json が対応するdocumentTypeを持つ場合はそちらを唯一の真実源にする
                    # （x-render-target.deployは読まない。真実源が2箇所に分散するのを避けるため）
                    for dp, mode in tool_targets:
                        if mode == "symlink":
                            self._documents.link(canonical, dp)
                        else:
                            self._documents.write_text(dp, output)
                        deployed.append(dp)
                else:
                    # deploy: 同一フォーマットは verbatim copy（更新漏れ防止のため render に内蔵）。
                    # deployテンプレートが参照する変数がpath_varsに無い場合（例: skillRef未宣言の
                    # document）、そのdeploy先だけをスキップする（canonicalの書き込みは妨げない）。
                    for dep in _select_deploy(target.get("deploy", []), spec_kind):
                        try:
                            dp = path_template.resolve(dep, **path_vars)
                        except KeyError:
                            continue
                        self._documents.write_text(dp, output)
                        deployed.append(dp)
            except OSError as e:
                return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")

        return Ok({
            "path": canonical, "deployed": deployed, "format": fmt, "content": output,
        })

    def _resolve_tool_deploy_targets(
        self, document_type: str | None, path_vars: dict, spec_kind: str | None,
    ) -> list[tuple[str, str]] | None:
        """.waffle/config.json の toolMappings から documentType 向けのdeploy先を解決する。

        config.json が無い、または documentType に対応するマッピングが1つも無ければ None を返し、
        呼び出し元は従来通り x-render-target.deploy を読む（後方互換フォールバック）。
        1つでも対応があれば、そのdocumentTypeについては config.json を唯一の真実源として扱う。
        """
        try:
            raw = self._documents.read_text(".waffle/config.json")
        except (OSError, FileNotFoundError):
            return None
        try:
            config = json.loads(raw)
        except json.JSONDecodeError:
            return None

        targets: list[tuple[str, str]] = []
        for tool_config in config.get("toolMappings", {}).values():
            mapping = tool_config.get(document_type) if document_type else None
            mapping = _select_field_map(mapping, spec_kind) if mapping else mapping
            if not mapping:
                continue
            mode = mapping.get("mode", "render")
            array_vars = {k: v for k, v in path_vars.items() if isinstance(v, list)}
            if array_vars:
                # 複数の値を持つpathVar（例: 複数advisorへのskillRefs）は、要素ごとに
                # 1つずつdeploy先を解決する（fan-out）。値が配列のpathVarは高々1種類を想定
                # （実例1件・KnowledgeSchemaのskillRefsのみのため、2種類以上の組合せ展開は
                # 未サポート。evidence-based-scope: 実証済みの拡張の範囲に限定する）。
                var_name, values = next(iter(array_vars.items()))
                for value in values:
                    scalar_vars = {**path_vars, var_name: value}
                    try:
                        dp = path_template.resolve(mapping["pathTemplate"], **scalar_vars)
                    except KeyError:
                        continue
                    targets.append((dp, mode))
            else:
                try:
                    dp = path_template.resolve(mapping["pathTemplate"], **path_vars)
                except KeyError:
                    continue
                targets.append((dp, mode))
        return targets or None

    def _resolve_path_vars(self, doc: dict, schema: dict, document_path: str, spec_kind: str | None) -> dict:
        """x-render-target のパステンプレートに渡す変数を組み立てる。

        x-source-target が specKind 等でネストしている場合、contextRef のような
        「document には保存しない」変数は、実際の document_path をそのテンプレートに
        逆解析して復元する（create 時に渡した値は保存せず、パスそのものから読み戻す）。
        """
        path_vars = {"documentId": doc["documentId"]}
        x_source = schema.get("x-source-target")
        if isinstance(x_source, dict):
            key = discriminator_key(schema)
            template = x_source.get(doc.get(key)) if key else None
            if template:
                recovered = path_template.reverse_parse(template, document_path)
                if recovered:
                    path_vars.update(recovered)
        path_vars_decl = _select_field_map(schema.get("x-render-target", {}).get("pathVars", {}), spec_kind)
        for var_name, dotted_path in path_vars_decl.items():
            try:
                path_vars[var_name] = _resolve_path({"doc": doc}, dotted_path)
            except KeyError:
                continue  # このdocumentには当該フィールドが無い→この変数を使うdeploy先だけ後段でスキップされる
        return path_vars

    def _render_frontmatter(self, doc: dict, schema: dict, spec_kind: str | None) -> str:
        fm = _select_field_map(schema.get("x-frontmatter") or {}, spec_kind)
        if not fm:
            return ""
        lines = ["---"]
        for key, path in fm.items():
            try:
                value = _resolve_path({"doc": doc}, path)
            except KeyError:
                continue  # 任意ブロック省略時：値で埋めずフィールドごと省略する（上書き指定の意味を保つ）
            value = _normalize_frontmatter_value(value)
            if not value:
                continue  # 空文字・空配列・null も同様に省略する（part_rendererの空値省略規約と一貫）
            # JSON 文字列は YAML のスカラとしても安全（コロン・括弧・日本語を含んでも壊れない）
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        if len(lines) == 1:
            return ""  # 全フィールドが省略された場合は frontmatter 自体を出さない
        lines.append("---")
        return "\n".join(lines) + "\n\n"

    def _render_body(self, doc: dict, defs: dict) -> str:
        return _render_body_service(doc.get("content", {}), defs)

def _resolve_path(root: dict, path: str):
    """'doc.content.purpose.text' のようなドット区切りパスで dict を辿り値を返す。

    x-frontmatter は各 schema が『フィールド→パス』を宣言する（ロジックはデータに置かず
    描画は engine が担う＝Harness 原則）。新しい frontmatter パターンはこの宣言を増やすだけで対応する。
    """
    cur = root
    for part in path.split("."):
        cur = cur[part]
    return cur

def _normalize_frontmatter_value(value):
    """text/items のいずれかを持つブロック形状の dict（DescriptionBlock/SummaryBlock等）を
    単一のスカラ値へ正規化する。text があればそれを使い、無ければ items を半角スペースで
    結合する（schema名に依存せず、値の形だけで判定する＝Harness原則を保つ）。"""
    if isinstance(value, dict) and ("text" in value or "items" in value):
        return value.get("text") or " ".join(value.get("items", []))
    return value

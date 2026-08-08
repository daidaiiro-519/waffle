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
from waffle.domain.services import deploy_target_resolution, path_template
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

def _config_declares(tool_mappings: dict, document_type: str | None) -> bool:
    """toolMappingsが、そのdocumentTypeの宣言を（役割を問わず）1つでも持つか。"""
    if not document_type:
        return False
    return any(
        document_type in by_document_type
        for tool_config in tool_mappings.values()
        for by_document_type in tool_config.values()
        if isinstance(by_document_type, dict)
    )


class RenderDocument:
    """documentを成果物へ描画し、宣言された配置先へ置く。"""
    def __init__(
        self,
        documents: DocumentRepository,
        schemas: SchemaRepository,
    ) -> None:
        self._documents = documents
        self._schemas = schemas
        self._schema_cache: list[dict] | None = None

    def run(self, document_path: str, deploy: bool = True) -> Result[dict]:
        """documentを成果物へ描画し、宣言された配置先へ置く。

        Args:
            document_path: 対象とするdocumentの置き場所。
            deploy: 描画した成果物を、schemaが定める配置先へ置くかどうか。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
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
        skipped: list[dict] = []
        if deploy and canonical:
            targets, resolve_skipped = self._resolve_deploy_targets(doc, target, path_vars, spec_kind)
            skipped.extend(resolve_skipped)
            conflict = self._find_ownership_conflict(doc["documentId"], targets)
            if conflict is not None:
                dp, owner = conflict
                return _err(
                    "DEPLOY_TARGET_OWNED_BY_OTHER",
                    f"{dp} は既に {owner} の成果物です。1つの配置先は1つのDocumentにのみ所有されます",
                )
            try:
                # canonical（.waffle 配下）に書く
                self._documents.write_text(canonical, output)
                for dp, mode in targets:
                    if mode == "symlink":
                        self._documents.link(canonical, dp)
                    else:
                        self._documents.write_text(dp, output)
                    deployed.append(dp)
            except OSError as e:
                return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")

        return Ok({
            "path": canonical, "deployed": deployed, "skipped": skipped,
            "format": fmt, "content": output,
        })

    def _resolve_deploy_targets(
        self, doc: dict, target: dict, path_vars: dict, spec_kind: str | None,
    ) -> tuple[list[tuple[str, str]], list[dict]]:
        """配置先を解決する。

        .waffle/config.json の toolMappings が対象documentTypeの宣言を持てば、そちらを
        唯一の真実源にする（x-render-target.deployは読まない。真実源が2箇所に分散するのを
        避けるため）。宣言を持たないdocumentTypeについてのみ、schema側のdeployを読む。

        判定を「そのdocumentTypeの宣言があるか」で行うのは、解決キー（役割・discriminator）
        に対応する宣言が無いことを、schema側へのフォールバックと取り違えないため。雛形は
        まさにこの「documentTypeの宣言はあるが、自分の役割の宣言は無い」状態に置かれる。
        """
        tool_mappings = self._load_tool_mappings()
        document_type = doc.get("documentType")
        document_role = doc.get("documentRole", deploy_target_resolution.DEFAULT_DOCUMENT_ROLE)
        if _config_declares(tool_mappings, document_type):
            mappings = deploy_target_resolution.select_mappings(
                tool_mappings, document_type, document_role, spec_kind,
            )
        else:
            mappings = [
                {"pathTemplate": dep, "mode": "render"}
                for dep in _select_deploy(target.get("deploy", []), spec_kind)
            ]

        targets: list[tuple[str, str]] = []
        skipped: list[dict] = []
        for mapping in mappings:
            resolved, unresolved = deploy_target_resolution.resolve_targets(mapping, path_vars)
            targets.extend(resolved)
            skipped.extend(unresolved)
        return targets, skipped

    def _find_ownership_conflict(
        self, document_id: str, targets: list[tuple[str, str]],
    ) -> tuple[str, str] | None:
        """配置先のいずれかが他のDocumentの成果物であれば、その配置先と所有者を返す。"""
        if not targets:
            return None
        templates = deploy_target_resolution.canonical_templates(self._all_schemas())
        for dp, _mode in targets:
            real = self._documents.resolve_real_path(dp)
            if not real:
                continue  # まだ何も置かれていない配置先は、誰にも所有されていない
            projection = deploy_target_resolution.find_projection(templates, real)
            if projection and projection[1] != document_id:
                return dp, projection[1]
        return None

    def _all_schemas(self) -> list[dict]:
        """出荷されている全schemaを読み込む（canonicalテンプレートの収集用）。"""
        if self._schema_cache is None:
            loaded: list[dict] = []
            for name in self._schemas.list_names():
                for version in self._schemas.list_versions(name):
                    try:
                        loaded.append(self._schemas.load(f"{name}/{version}"))
                    except (FileNotFoundError, ValueError):
                        continue
            self._schema_cache = loaded
        return self._schema_cache

    def _load_tool_mappings(self) -> dict:
        """.waffle/config.json の toolMappings を返す。読めなければ空。"""
        try:
            config = json.loads(self._documents.read_text(".waffle/config.json"))
        except (OSError, FileNotFoundError, json.JSONDecodeError):
            return {}
        return config.get("toolMappings", {})

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

"""render blank template — schemaRef（と必要ならdiscriminator）から、値を一切埋めていない
content構造を、各フィールドのx-prompt-write本文を{{...}}プレースホルダーとして埋め込んだ
Markdownとして描画し、schemaRef・discriminatorから機械的に導出したパスへファイルとして
書き出す application use case（uc-render-blank-template）。

scaffold createが使うskeleton/fillTemplateの機械走査（domain/services/fill_template）と、
render-documentが使う本文描画（domain/services/part_renderer.render_body）を合成し、
render-documentと同じくpath_template.resolveでパスを導出してファイル書き込みまで行う。
document.jsonの読み書きは行わない（書き出すのはプレースホルダーMarkdownのみ）。

schemaがx-frontmatterを宣言する場合、本文と同じ要領でfrontmatterもプレースホルダー
として先頭に付ける（render-documentのx-frontmatterは実際の値を解決するが、blank
templateには値が無いため、対応するフィールドのx-prompt-write本文をプレースホルダーに
する）。x-frontmatterが無ければfrontmatterブロック自体を省略する。
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_schema
from waffle.domain.services import path_template
from waffle.domain.services.fill_template import build_fill_template, build_skeleton, build_top_level_fill_template
from waffle.domain.services.fill_template import content_def as _content_def
from waffle.domain.services.fill_template import discriminator_candidates, overlay_placeholders
from waffle.domain.services.part_renderer import render_body
from waffle.domain.services.schema_discriminator import discriminator_key
from waffle.shared.result import Err, Ok, Result

_DOCUMENT_ID_PROMPT = "この文書を一意に識別する識別子。"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _select_field_map(value: dict, spec_kind: str | None) -> dict:
    """render_document.pyの同名関数と同じ選択規則（discriminatorごとの入れ子か
    フラットかを値の形から判定する）。x-frontmatterの解決に使う。"""
    if value and all(isinstance(v, dict) for v in value.values()):
        return value.get(spec_kind, {}) if spec_kind else {}
    return value


def _render_frontmatter_placeholders(schema: dict, spec_kind: str | None, prompt_by_path: dict) -> str:
    fm = _select_field_map(schema.get("x-frontmatter") or {}, spec_kind)
    if not fm:
        return ""
    lines = ["---"]
    for key, path in fm.items():
        content_path = path[4:] if path.startswith("doc.") else path
        # x-frontmatterはtext/itemsを持つブロックそのもの（例: doc.content.description）を
        # 指すことがある（render_documentの_normalize_frontmatter_valueと同型の規約）。
        # そのブロック自身にはx-prompt-writeが無く、実際の値を持つitems/textの方に
        # x-prompt-writeが宣言されているため、無ければそちらへフォールバックする。
        prompt = (
            prompt_by_path.get(content_path)
            or prompt_by_path.get(f"{content_path}.items")
            or prompt_by_path.get(f"{content_path}.text")
            or (_DOCUMENT_ID_PROMPT if content_path == "documentId" else None)
        )
        if prompt is None:
            continue
        lines.append(f"{key}: {json.dumps(f'{{{{{prompt}}}}}', ensure_ascii=False)}")
    if len(lines) == 1:
        return ""
    lines.append("---")
    return "\n".join(lines) + "\n\n"


class RenderBlankTemplate:
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository) -> None:
        self._documents = documents
        self._schemas = schemas

    def run(self, schema_ref: str, discriminator: dict | None = None) -> Result[dict]:
        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = discriminator_key(schema)
        discriminator = discriminator or {}
        if disc_key:
            candidates = discriminator_candidates(schema, disc_key)
            if disc_key not in discriminator:
                return _err("MISSING_DISCRIMINATOR", f"{disc_key} の指定が必要です（候補: {', '.join(candidates)}）")
            if discriminator[disc_key] not in candidates:
                return _err(
                    "INVALID_DISCRIMINATOR",
                    f"{disc_key}='{discriminator[disc_key]}' は不正な値です（候補: {', '.join(candidates)}）",
                )

        spec_kind = discriminator.get(disc_key) if disc_key else None
        content_def = _content_def(schema, discriminator)
        skeleton = build_skeleton(schema, "{{documentId}}", disc_key, discriminator, content_def, {})
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        entries = (
            build_top_level_fill_template(schema, protected, spec_kind)
            + build_fill_template(schema, content_def, spec_kind)
        )
        placeholder_doc = overlay_placeholders(skeleton, entries)

        prompt_by_path = {e["path"]: e["prompt"] for e in entries}
        frontmatter = _render_frontmatter_placeholders(schema, spec_kind, prompt_by_path)

        defs = schema.get("$defs", {})
        output = frontmatter + render_body(placeholder_doc.get("content", {}), defs)

        path = path_template.blank_template_path(schema_ref, discriminator)
        try:
            self._documents.write_text(path, output)
        except OSError as e:
            return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")
        return Ok({"content": output, "path": path})

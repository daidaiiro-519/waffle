"""render blank template — schemaRef（と必要ならdiscriminator）から、値を一切埋めていない
content構造を、各フィールドのx-prompt-write本文を{{...}}プレースホルダーとして埋め込んだ
Markdownとして描画する application use case（uc-render-blank-template）。

scaffold createが使うskeleton/fillTemplateの機械走査（domain/services/fill_template）と、
render-documentが使う本文描画（domain/services/part_renderer.render_body）を、そのまま
合成するだけの薄い編成。document.jsonの読み書きは一切行わない（副作用なし）。
"""
from __future__ import annotations

from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.services.document_loading import load_schema
from waffle.domain.services.fill_template import build_fill_template, build_skeleton, build_top_level_fill_template
from waffle.domain.services.fill_template import content_def as _content_def
from waffle.domain.services.fill_template import discriminator_candidates, overlay_placeholders
from waffle.domain.services.part_renderer import render_body
from waffle.domain.services.schema_discriminator import discriminator_key
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class RenderBlankTemplate:
    def __init__(self, schemas: SchemaRepository) -> None:
        self._schemas = schemas

    def run(self, schema_ref: str, discriminator: dict | None = None) -> Result[dict]:
        schema_result = load_schema(self._schemas, schema_ref)
        if isinstance(schema_result, Err):
            return schema_result
        schema = schema_result.value

        disc_key = discriminator_key(schema)
        discriminator = discriminator or {}
        if disc_key and disc_key not in discriminator:
            cands = ", ".join(discriminator_candidates(schema, disc_key))
            return _err("MISSING_DISCRIMINATOR", f"{disc_key} の指定が必要です（候補: {cands}）")

        content_def = _content_def(schema, discriminator)
        skeleton = build_skeleton(schema, "{{documentId}}", disc_key, discriminator, content_def, {})
        protected = {"documentId"} | ({disc_key} if disc_key else set())
        entries = build_top_level_fill_template(schema, protected) + build_fill_template(schema, content_def)
        placeholder_doc = overlay_placeholders(skeleton, entries)

        defs = schema.get("$defs", {})
        output = render_body(placeholder_doc.get("content", {}), defs)
        return Ok({"content": output})

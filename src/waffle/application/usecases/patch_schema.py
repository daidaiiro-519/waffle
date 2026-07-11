"""patch schema — Schema定義ファイル自体への構造化編集(add_block/rename_block)。

Harness原則をSchema自体に適用する: AIはブロック定義・識別子名だけを与え、対象外の箇所は
一切変更しない。書き込み前に後方互換チェック・JSON Schema構文検証を必ず通す。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.application.ports.validator import Validator
from waffle.domain.services import schema_patch
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class PatchSchema:
    def __init__(self, documents: DocumentRepository, schemas: SchemaRepository, validator: Validator) -> None:
        self._documents = documents
        self._schemas = schemas
        self._validator = validator

    def run(self, operation: str, params: dict) -> Result[dict]:
        schema_ref = params.get("schemaRef")
        if not schema_ref:
            return _err("MISSING_PARAM", "schemaRef が必要です")

        try:
            path = self._schemas.resolve_path(schema_ref)
        except FileNotFoundError:
            return _err("INVALID_SCHEMA_REF", f"schemaRef を解決できません: {schema_ref}")

        old_schema = self._schemas.load(schema_ref)

        if operation == "add_block":
            required = ("blockName", "blockDef", "contentDefName", "propName")
            if not all(params.get(k) for k in required):
                return _err("MISSING_PARAM", f"add_block には {', '.join(required)} が必要です")
            new_schema = schema_patch.add_block(
                old_schema,
                params["blockName"],
                params["blockDef"],
                params["contentDefName"],
                params["propName"],
                required=bool(params.get("required", False)),
            )
        elif operation == "rename_block":
            if not params.get("oldName") or not params.get("newName"):
                return _err("MISSING_PARAM", "rename_block には oldName, newName が必要です")
            try:
                new_schema = schema_patch.rename_block(old_schema, params["oldName"], params["newName"])
            except schema_patch.BlockNotFoundError as e:
                return _err("BLOCK_NOT_FOUND", str(e))
        else:
            return _err("INVALID_OPERATION", f"未知の operation: {operation}")

        violations = schema_patch.check_backward_compatible(old_schema, new_schema)
        if violations:
            return _err("BACKWARD_INCOMPATIBLE", "; ".join(violations))

        structure_errors = self._validator.check_schema(new_schema)
        if structure_errors:
            return _err("INVALID_SCHEMA_STRUCTURE", "; ".join(structure_errors))

        output = schema_patch.dump(new_schema)
        changed = output != schema_patch.dump(old_schema)
        if changed:
            self._documents.write_text(path, output)
        return Ok({"schemaRef": schema_ref, "path": path, "changed": changed})

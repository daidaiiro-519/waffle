"""patch schema — Schema定義ファイル自体への構造化編集(add_block/rename_block)。

Harness原則をSchema自体に適用する: AIはブロック定義・識別子名だけを与え、対象外の箇所は
一切変更しない。書き込み前に後方互換チェック・JSON Schema構文検証を必ず通す。
"""
from __future__ import annotations

from pathlib import Path

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
        if operation == "create_version":
            return self._create_version(params)

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
        elif operation == "set_field":
            # defNameはNoneでもよい（schemaのルート直下を対象にする合図）。
            # fieldPath/valueは常に必須。
            if not params.get("fieldPath") or "value" not in params or "defName" not in params:
                return _err("MISSING_PARAM", "set_field には defName, fieldPath, value が必要です")
            try:
                new_schema = schema_patch.set_field(old_schema, params["defName"], params["fieldPath"], params["value"])
            except schema_patch.BlockNotFoundError as e:
                return _err("BLOCK_NOT_FOUND", str(e))
        elif operation == "remove_block":
            required = ("contentDefName", "propName")
            if not all(params.get(k) for k in required):
                return _err("MISSING_PARAM", f"remove_block には {', '.join(required)} が必要です")
            try:
                new_schema = schema_patch.remove_block(old_schema, params["contentDefName"], params["propName"])
            except schema_patch.BlockNotFoundError as e:
                return _err("BLOCK_NOT_FOUND", str(e))
        elif operation == "add_def":
            required = ("defName", "defDef")
            if not all(params.get(k) for k in required):
                return _err("MISSING_PARAM", f"add_def には {', '.join(required)} が必要です")
            new_schema = schema_patch.add_def(old_schema, params["defName"], params["defDef"])
        elif operation == "add_kind_branch":
            required = ("discriminatorField", "kindValue", "contentDefName")
            if not all(params.get(k) for k in required):
                return _err("MISSING_PARAM", f"add_kind_branch には {', '.join(required)} が必要です")
            try:
                new_schema = schema_patch.add_kind_branch(
                    old_schema, params["discriminatorField"], params["kindValue"], params["contentDefName"]
                )
            except schema_patch.UnsupportedRootDispatchShapeError as e:
                return _err("UNSUPPORTED_ROOT_DISPATCH_SHAPE", str(e))
        elif operation == "set_kind_render_target":
            required = ("kindValue", "pathVars", "path", "deploy")
            if not all(params.get(k) for k in required):
                return _err("MISSING_PARAM", f"set_kind_render_target には {', '.join(required)} が必要です")
            try:
                new_schema = schema_patch.set_kind_render_target(
                    old_schema, params["kindValue"], params["pathVars"], params["path"], params["deploy"]
                )
            except schema_patch.UnsupportedRenderTargetShapeError as e:
                return _err("UNSUPPORTED_RENDER_TARGET_SHAPE", str(e))
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
            try:
                self._documents.write_text(path, output)
            except OSError as e:
                return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")
        return Ok({"schemaRef": schema_ref, "path": path, "changed": changed})

    def _create_version(self, params: dict) -> Result[dict]:
        to_ref = params.get("schemaRef")
        from_ref = params.get("fromSchemaRef")
        if not to_ref or not from_ref:
            return _err("MISSING_PARAM", "create_version には schemaRef（新版）, fromSchemaRef（複製元）が必要です")

        try:
            from_path = self._schemas.resolve_path(from_ref)
        except FileNotFoundError:
            return _err("INVALID_SCHEMA_REF", f"fromSchemaRef を解決できません: {from_ref}")

        to_name = to_ref.split("/")[-1]
        to_path = str(Path(from_path).with_name(f"{to_name}.json"))
        if Path(to_path).is_file():
            return _err("VERSION_ALREADY_EXISTS", f"schemaRef は既に存在します: {to_ref}")

        base_schema = self._schemas.load(from_ref)
        new_schema = schema_patch.create_version(base_schema, params.get("edits", []))

        structure_errors = self._validator.check_schema(new_schema)
        if structure_errors:
            return _err("INVALID_SCHEMA_STRUCTURE", "; ".join(structure_errors))

        output = schema_patch.dump(new_schema)
        try:
            self._documents.write_text(to_path, output)
        except OSError as e:
            return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")
        return Ok({"schemaRef": to_ref, "path": to_path, "changed": True})

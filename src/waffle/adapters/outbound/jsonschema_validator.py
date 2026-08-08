"""jsonschema による検証 adapter（Validator 実装）。

外部 library(jsonschema) はこの outbound adapter にのみ閉じ込める（lib-via-adapter 規約）。
"""
from __future__ import annotations

from jsonschema import Draft202012Validator

from waffle.application.ports.validator import Validator


class JsonSchemaValidator(Validator):
    """schemaへの適合判定を、既存のJSON Schema実装で行う。"""
    def validate(self, document: dict, schema: dict) -> list[str]:
        """documentがschemaに適合しているかを判じる。

        Args:
            document: 判じる対象のdocument。
            schema: 照らす相手のschema。

        Returns:
            適合しない箇所の説明の一覧。適合していれば空。

        Raises:
            なし。
        """
        v = Draft202012Validator(schema)
        errors = sorted(v.iter_errors(document), key=lambda e: list(e.path))
        return [f"{list(e.path)}: {e.message}" for e in errors]

    def check_schema(self, schema: dict) -> list[str]:
        """schema自体が、schemaとして正しい形かを判じる。

        Args:
            schema: 判じる対象のschema。

        Returns:
            正しくない箇所の説明の一覧。正しければ空。

        Raises:
            なし。
        """
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as e:  # jsonschema.exceptions.SchemaError
            return [str(e)]
        return []

"""テスト全体で共有する偽実装（テストダブル）を提供する。

偽実装をテストごとに定義すると、本物の port 実装と少しずつ食い違い、
その食い違いに気づかないままテストが緑になる。実際に SchemaRepository の
偽実装が4つに分かれ、3つが load の失敗を再現せず、3つが resolve_path を
持たないまま残っていた。

偽実装は1箇所にだけ置き、同じ契約テストスイート
（tests/integration/test_schema_repository_contract.py）を本物と偽実装の
両方に当てて、両者が同じ契約を満たすことを確かめる。
"""
from __future__ import annotations

# 契約テストで使う、実際にパッケージへ同梱されている schema。
CONTRACT_SCHEMA_NAME = "CodingSchema"
CONTRACT_SCHEMA_VERSION = "v4"
CONTRACT_SCHEMA_REF = f"{CONTRACT_SCHEMA_NAME}/{CONTRACT_SCHEMA_VERSION}"
MISSING_SCHEMA_REF = "NoSuchSchema/v9"


class FakeSchemaRepository:
    """SchemaRepository の偽実装。契約は PackageSchemaRepository と揃える。

    与えられた schemaRef の辞書だけを知っている。知らない schemaRef に対しては
    本物と同じく FileNotFoundError を送出する。list_versions と resolve_path も
    同じ辞書から導出するため、load が知らない版を list_versions が返すような
    自己矛盾は起こらない。

    Args:
        schemas: schemaRef（例: "CodingSchema/v4"）から schema 本体への辞書。
    """

    def __init__(self, schemas: dict[str, dict]) -> None:
        self._schemas = dict(schemas)

    def load(self, schema_ref: str) -> dict:
        """schemaRef から schema を返す。

        Args:
            schema_ref: 解決する schemaRef。

        Returns:
            schema 本体。

        Raises:
            FileNotFoundError: その schemaRef を知らない場合。
        """
        if schema_ref not in self._schemas:
            raise FileNotFoundError(schema_ref)
        return self._schemas[schema_ref]

    def list_versions(self, name: str) -> list[str]:
        """name 配下に存在する版識別子の一覧を返す。

        Args:
            name: schema 名（例: "CodingSchema"）。

        Returns:
            版識別子の一覧。知らない name なら空配列。
        """
        prefix = f"{name}/"
        return sorted(ref[len(prefix):] for ref in self._schemas if ref.startswith(prefix))

    def resolve_path(self, schema_ref: str) -> str:
        """schemaRef が存在するファイルパスを返す。

        Args:
            schema_ref: 解決する schemaRef。

        Returns:
            ファイルパス。

        Raises:
            FileNotFoundError: その schemaRef を知らない場合。
        """
        if schema_ref not in self._schemas:
            raise FileNotFoundError(schema_ref)
        return f"{schema_ref}.json"


# 検査が読む命名規約の宣言。テストは「どの規約のもとで検査するか」を明示する。
PYTHON_NAMING = {
    "fileNameDerivedFrom": "type",
    "fileNameTransform": "pascal-to-snake",
    "fileNameSuffix": "." + "py",
    "cases": [
        {"artifact": "module", "case": "snake"},
        {"artifact": "type", "case": "pascal"},
        {"artifact": "function", "case": "snake"},
        {"artifact": "field", "case": "snake"},
    ],
}

JAVA_NAMING = {
    "fileNameDerivedFrom": "type",
    "fileNameTransform": "identity",
    "fileNameSuffix": ".java",
    "cases": [
        {"artifact": "type", "case": "pascal"},
        {"artifact": "function", "case": "camel"},
        {"artifact": "field", "case": "camel"},
    ],
}

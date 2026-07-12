"""uc-render-blank-template の受け入れテスト（ネイティブpytest）。"""
from waffle.application.usecases.render_blank_template import RenderBlankTemplate
from waffle.shared.result import Err, Ok


class _FakeSchemaRepository:
    def __init__(self, schemas: dict[str, dict]) -> None:
        self._schemas = schemas

    def load(self, schema_ref: str) -> dict:
        if schema_ref not in self._schemas:
            raise FileNotFoundError(schema_ref)
        return self._schemas[schema_ref]

    def list_versions(self, name: str) -> list[str]:
        return []

    def resolve_path(self, schema_ref: str) -> str:
        return schema_ref


def _engine(schemas: dict[str, dict]) -> RenderBlankTemplate:
    return RenderBlankTemplate(_FakeSchemaRepository(schemas))


def _simple_schema() -> dict:
    return {
        "required": ["documentId", "content"],
        "properties": {
            "documentId": {"type": "string"},
            "content": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"$ref": "#/$defs/TitleBlock"},
                },
            },
        },
        "$defs": {
            "TitleBlock": {
                "type": "object",
                "required": ["blockType", "title"],
                "x-render-order": 1,
                "x-render-level": 2,
                "x-render": [{"as": "paragraph", "from": "title"}],
                "properties": {
                    "blockType": {"type": "string", "const": "Title"},
                    "title": {"type": "string", "x-prompt-write": "タイトルを書く"},
                },
            },
        },
    }


def test_スキーマの値フィールドをプレースホルダー化したMarkdownを返す():
    """
    Given x-prompt-writeを宣言する値フィールドを持つschema
    When そのschemaRefでブランクテンプレート描画を実行する
    Then 返り値のMarkdownには、各値フィールドの位置にx-prompt-write本文を含む{{...}}形式のプレースホルダーが描画されている
    """
    result = _engine({"SimpleSchema/v1": _simple_schema()}).run("SimpleSchema/v1")
    assert isinstance(result, Ok), result
    assert "{{タイトルを書く}}" in result.value["content"]


def test_存在しないschemaRefはINVALID_SCHEMA_REF():
    """
    Given 実在しないschemaRef
    When ブランクテンプレート描画を実行する
    Then INVALID_SCHEMA_REFエラーが返る
    """
    result = _engine({}).run("NotASchema/v1")
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_SCHEMA_REF"


def test_discriminator未指定はMISSING_DISCRIMINATOR():
    """
    Given contentがdiscriminatorで分岐するschema
    When discriminatorを指定せずにブランクテンプレート描画を実行する
    Then MISSING_DISCRIMINATORエラーが返る
    """
    schema = {
        "required": ["documentId", "kind", "content"],
        "properties": {
            "documentId": {"type": "string"},
            "kind": {"type": "string", "enum": ["a", "b"]},
        },
        "allOf": [
            {
                "if": {"properties": {"kind": {"const": "a"}}, "required": ["kind"]},
                "then": {"properties": {"content": {"$ref": "#/$defs/AContent"}}},
            },
        ],
        "$defs": {
            "AContent": {
                "type": "object", "required": [],
                "properties": {},
            },
        },
    }
    result = _engine({"DiscSchema/v1": schema}).run("DiscSchema/v1")
    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_DISCRIMINATOR"


def test_enumフィールドは選択肢を併記する():
    """
    Given enumを宣言する値フィールドを持つschema
    When そのschemaRefでブランクテンプレート描画を実行する
    Then プレースホルダー文字列に選択肢一覧が含まれている
    """
    schema = _simple_schema()
    schema["$defs"]["TitleBlock"]["properties"]["title"]["enum"] = ["A", "B"]
    result = _engine({"EnumSchema/v1": schema}).run("EnumSchema/v1")
    assert isinstance(result, Ok), result
    assert "{{タイトルを書く（選択肢: A / B）}}" in result.value["content"]


def test_構造化配列要素は1件分のプレースホルダーとして描画する():
    """
    Given 配列フィールドが構造化された要素(オブジェクト)を宣言するschema
    When そのschemaRefでブランクテンプレート描画を実行する
    Then 要素1件分のプレースホルダーオブジェクトを含む配列として描画される
    """
    schema = {
        "required": ["documentId", "content"],
        "properties": {
            "documentId": {"type": "string"},
            "content": {
                "type": "object",
                "required": ["errors"],
                "properties": {
                    "errors": {"$ref": "#/$defs/ErrorsBlock"},
                },
            },
        },
        "$defs": {
            "ErrorsBlock": {
                "type": "object",
                "required": ["blockType", "title", "items"],
                "x-render-order": 1,
                "x-render-level": 2,
                "x-render": [{"as": "table", "from": "items", "columns": [
                    {"field": "code", "header": "コード"}, {"field": "condition", "header": "条件"},
                ]}],
                "properties": {
                    "blockType": {"type": "string", "const": "Errors"},
                    "title": {"type": "string", "const": "エラー"},
                    "items": {
                        "type": "array",
                        "x-prompt-write": "エラーを列挙",
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "x-prompt-write": "エラーコード"},
                                "condition": {"type": "string", "x-prompt-write": "発生条件"},
                            },
                        },
                    },
                },
            },
        },
    }
    result = _engine({"ArraySchema/v1": schema}).run("ArraySchema/v1")
    assert isinstance(result, Ok), result
    assert "{{エラーコード}}" in result.value["content"]
    assert "{{発生条件}}" in result.value["content"]


def test_document_jsonへの書き込みを一切行わない():
    """
    Given schemaのみを受け取るブランクテンプレート描画
    When 実行する
    Then documentRepositoryを一切要求しない（副作用の無い読み取り専用の描画）
    """
    engine = RenderBlankTemplate(_FakeSchemaRepository({"SimpleSchema/v1": _simple_schema()}))
    result = engine.run("SimpleSchema/v1")
    assert isinstance(result, Ok), result
    assert set(result.value.keys()) == {"content"}

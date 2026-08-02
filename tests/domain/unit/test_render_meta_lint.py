"""x-render 宣言を RenderMetaSchema へ照合する補助関数のテスト。

agg-schema の invariantScenarios には対応しない。宣言されたシナリオに
紐づかないテストを同じファイルへ混ぜると、そのテストが常に孤立として
報告され続け、警報が意味を失うため別ファイルに置く。
"""
from waffle.adapters.outbound.jsonschema_validator import JsonSchemaValidator
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository


def _lint_render(parts):
    meta = PackageSchemaRepository().load("RenderMetaSchema/v1")
    schema = {"$defs": meta["$defs"], "type": "array", "items": {"$ref": "#/$defs/RenderPart"}}
    return JsonSchemaValidator().validate(parts, schema)


def test_lint_accepts_valid():
    """語彙に沿った部品宣言は不適合を返さない。"""
    assert _lint_render([{"as": "paragraph", "from": "text"},
                         {"as": "table", "from": "rows", "columns": [{"field": "name"}]}]) == []


def test_lint_rejects_unknown_part():
    """未知の部品種別は enum 違反として検出される。"""
    assert _lint_render([{"as": "foobar", "from": "x"}])


def test_lint_rejects_missing_required_attr():
    """必須属性（table の columns）が欠けていれば検出される。"""
    assert _lint_render([{"as": "table", "from": "rows"}])

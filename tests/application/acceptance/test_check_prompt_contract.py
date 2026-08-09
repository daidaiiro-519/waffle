"""uc-check-prompt-contract の受け入れテスト（ネイティブpytest）。

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。
"""
from waffle.application.usecases.check_prompt_contract import CheckPromptContract
from waffle.shared.result import Ok


class FakeSchemas:
    """schemaRef から schema を返すだけの偽物。"""

    def __init__(self, schema: dict) -> None:
        self._schema = schema

    def load(self, schema_ref: str) -> dict:
        if schema_ref != "Fixture/v1":
            raise FileNotFoundError(schema_ref)
        return self._schema

    def list_versions(self, name: str) -> list:  # pragma: no cover — 使わない
        return ["v1"]

    def resolve_path(self, schema_ref: str) -> str:  # pragma: no cover — 使わない
        return schema_ref


def _run(schema: dict) -> dict:
    result = CheckPromptContract(FakeSchemas(schema)).run("Fixture/v1")
    assert isinstance(result, Ok), result
    return result.value


def _schema(block_defs: dict, content_props: dict) -> dict:
    return {
        "$defs": {**block_defs,
                  "Content": {"type": "object", "properties": content_props}},
        "properties": {"content": {"$ref": "#/$defs/Content"}},
    }


def _block(name: str, query: str | None = "読み方の指示", props: dict | None = None) -> dict:
    body = {"type": "object",
            "properties": {"blockType": {"const": name},
                           **(props or {"text": {"type": "string",
                                                 "x-prompt-write": "書き方の指示"}})}}
    if query is not None:
        body["x-prompt-query"] = query
    return body


def test_読み方の指示が無いブロックを見つける():
    """
    Scenario: 読み方の指示が無いブロックを見つける
    Given 読み方の指示を持たないブロックがあるスキーマ
    When 確認を求める
    Then そのブロックが、読み方の指示が無いものとして返る
    """
    schema = _schema({"TitleBlock": _block("Title", query=None)},
                     {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    assert [m["block"] for m in got["missing_query_prompts"]] == ["TitleBlock"]


def test_書き方の指示が無い記入対象を見つける():
    """
    Scenario: 書き方の指示が無い記入対象を見つける
    Given 書き方の指示を持たない記入対象があるスキーマ
    When 確認を求める
    Then その記入対象が、書き方の指示が無いものとして返る
    """
    schema = _schema(
        {"TitleBlock": _block("Title", props={"text": {"type": "string"}})},
        {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    assert [m["path"] for m in got["missing_write_prompts"]] == ["content.title.text"]


def test_契約に無い名前の指示を見つける():
    """
    Scenario: 契約に無い名前の指示を見つける
    Given x-prompt-query でも x-prompt-write でもない x-prompt- で始まるキーを持つスキーマ
    When 確認を求める
    Then そのキーが、契約に無い名前として返る
    """
    schema = _schema({"TitleBlock": _block("Title")},
                     {"title": {"$ref": "#/$defs/TitleBlock"}})
    schema["$defs"]["TitleBlock"]["x-prompt-interpret"] = "読まれない指示"

    got = _run(schema)

    assert [u["at"] for u in got["undeclared_prompt_keys"]] == [
        "/$defs/TitleBlock/x-prompt-interpret"]


def test_入れ子の奥にある記入対象も見落とさない():
    """
    Scenario: 入れ子の奥にある記入対象も見落とさない
    Given 配列の要素の中に、さらに記入対象を持つスキーマ
    And その記入対象には書き方の指示がある
    When 確認を求める
    Then その記入対象は、指示が無いものとして返らない
    """
    schema = _schema(
        {"EntitiesBlock": _block("Entities", props={"items": {
            "type": "array", "x-prompt-write": "エンティティを列挙",
            "items": {"type": "object", "properties": {
                "attributes": {
                    "type": "array", "x-prompt-write": "属性を列挙",
                    "items": {"type": "object", "properties": {
                        "name": {"type": "string", "x-prompt-write": "属性名"}}}}}}}})},
        {"entities": {"$ref": "#/$defs/EntitiesBlock"}})

    got = _run(schema)

    assert got["missing_write_prompts"] == []


def test_種別ごとに書き分けられた指示を欠落と数えない():
    """
    Scenario: 種別ごとに書き分けられた指示を欠落と数えない
    Given 書き方の指示が、種別ごとの対応表として書かれているスキーマ
    When 確認を求める
    Then その記入対象は、指示が無いものとして返らない
    """
    schema = _schema(
        {"TitleBlock": _block("Title", props={"text": {
            "type": "string",
            "x-prompt-write": {"usecase": "操作の名前", "aggregate": "集約の名前"}}})},
        {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    assert got["missing_write_prompts"] == []


def test_他所を指している欄は指し示す先で判定する():
    """
    Scenario: 他所を指している欄は、指し示す先で判定する
    Given 記入対象が他所の定義を指しており、指示はその先にあるスキーマ
    When 確認を求める
    Then その記入対象は、指示が無いものとして返らない
    """
    schema = _schema(
        {"LevelEnum": {"type": "string", "x-prompt-write": "強さを選ぶ"},
         "RulesBlock": _block("Rules", props={"level": {"$ref": "#/$defs/LevelEnum"}})},
        {"rules": {"$ref": "#/$defs/RulesBlock"}})

    got = _run(schema)

    assert got["missing_write_prompts"] == []


def test_固定された欄は記入対象に数えない():
    """
    Scenario: 固定された欄は記入対象に数えない
    Given 値が固定された欄を持つスキーマ
    When 確認を求める
    Then その欄は、指示が無いものとして返らない
    """
    schema = _schema({"TitleBlock": _block("Title")},
                     {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    # blockType は const で固定されているが、欠落として並ばない
    assert got["missing_write_prompts"] == []


def test_指示の中身が説明文でも欠落として返さない():
    """
    Scenario: 指示の中身が説明文でも欠落として返さない
    Given 読み方の指示が、読み方ではなく項目の説明になっているスキーマ
    When 確認を求める
    Then そのブロックは、指示が無いものとして返らない
    """
    schema = _schema({"TitleBlock": _block("Title", query="この文書の題名を持ちます。")},
                     {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    assert got["missing_query_prompts"] == []


def test_契約が守られていれば何も返らない():
    """
    Scenario: 契約が守られていれば何も返らない
    Given 3つの規則をすべて満たすスキーマ
    When 確認を求める
    Then どの一覧も空である
    """
    schema = _schema({"TitleBlock": _block("Title")},
                     {"title": {"$ref": "#/$defs/TitleBlock"}})

    got = _run(schema)

    assert got == {"missing_query_prompts": [], "missing_write_prompts": [],
                   "undeclared_prompt_keys": []}

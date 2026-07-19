"""query_path のユニットテスト（外部依存なしの判定ロジック）。

blockKey指定/省略時の分岐、正規表現カスタム関数(regex_match)、JMESPath構文エラー時の
Waffle独自エラーへの変換を、DocumentRepository/SchemaRepositoryを介さずに直接検証する。
"""
from waffle.application.usecases.query_document import _compile_jmespath, _evaluate, _query_path_all_blocks
from waffle.shared.result import Err, Ok


def test_正しい式はコンパイルできる():
    result = _compile_jmespath("items[?priority=='high'].name")
    assert isinstance(result, Ok)


def test_構文エラーの式はINVALID_JMESPATH_EXPRESSIONへ変換される():
    result = _compile_jmespath("items[?")
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_JMESPATH_EXPRESSION"


def test_単純な式を単一ブロックに対して評価できる():
    compiled = _compile_jmespath("items[?required==`true`]").value
    root = {"items": [{"name": "a", "required": True}, {"name": "b", "required": False}]}
    result = _evaluate(compiled, root)
    assert isinstance(result, Ok)
    assert result.value == [{"name": "a", "required": True}]


def test_regex_matchカスタム関数で絞り込める():
    compiled = _compile_jmespath("items[?regex_match(name, 'foo.*')]").value
    root = {"items": [{"name": "foobar"}, {"name": "baz"}]}
    result = _evaluate(compiled, root)
    assert isinstance(result, Ok)
    assert result.value == [{"name": "foobar"}]


def test_regex_matchに不正な正規表現を渡すとINVALID_JMESPATH_EXPRESSIONへ変換される():
    compiled = _compile_jmespath("items[?regex_match(name, '(')]").value
    root = {"items": [{"name": "foobar"}]}
    result = _evaluate(compiled, root)
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_JMESPATH_EXPRESSION"


def test_blockKey省略時は全ブロックへ相対式を評価しヒットしたものだけ集める():
    compiled = _compile_jmespath("items[?priority=='high']").value
    content = {
        "blockA": {"blockType": "X", "items": [{"name": "a", "priority": "high"}]},
        "blockB": {"blockType": "X", "items": [{"name": "b", "priority": "low"}]},
    }
    schema = {"$defs": {"XBlock": {"x-prompt-query": "dummy prompt"}}}
    result = _query_path_all_blocks(content, compiled, schema)
    assert isinstance(result, Ok)
    assert [r["blockKey"] for r in result.value] == ["blockA"]
    assert result.value[0]["prompt"] == "dummy prompt"
    assert result.value[0]["value"] == [{"name": "a", "priority": "high"}]


def test_blockKey省略時にヒットが1件も無ければ空配列になる():
    compiled = _compile_jmespath("items[?priority=='high']").value
    content = {
        "blockA": {"blockType": "X", "items": [{"name": "a", "priority": "low"}]},
    }
    schema = {"$defs": {"XBlock": {"x-prompt-query": "dummy prompt"}}}
    result = _query_path_all_blocks(content, compiled, schema)
    assert isinstance(result, Ok)
    assert result.value == []


def test_blockKey省略時に評価時型エラーになったブロックは黙ってスキップされ他のブロックの結果は返る():
    """items要素にruleフィールドを持たないブロック（blockB）ではcontains(rule, ...)が
    JMESPathTypeErrorになる。blockKey省略時はこれをハードエラーにせず、そのブロックだけ
    スキップして他のブロック（blockA）の結果は正常に返す。"""
    compiled = _compile_jmespath("items[?contains(rule, 'CLI')]").value
    content = {
        "blockA": {"blockType": "X", "items": [{"rule": "CLI経由で操作する"}, {"rule": "他のルール"}]},
        "blockB": {"blockType": "X", "items": [{"title": "ruleフィールドを持たない要素"}]},
    }
    schema = {"$defs": {"XBlock": {"x-prompt-query": "dummy prompt"}}}
    result = _query_path_all_blocks(content, compiled, schema)
    assert isinstance(result, Ok), result
    assert [r["blockKey"] for r in result.value] == ["blockA"]
    assert result.value[0]["value"] == [{"rule": "CLI経由で操作する"}]


def test_blockKey省略時に全ブロックが評価時型エラーでも正常系で空配列になる():
    compiled = _compile_jmespath("items[?contains(rule, 'CLI')]").value
    content = {
        "blockA": {"blockType": "X", "items": [{"title": "ruleフィールドを持たない要素"}]},
    }
    schema = {"$defs": {"XBlock": {"x-prompt-query": "dummy prompt"}}}
    result = _query_path_all_blocks(content, compiled, schema)
    assert isinstance(result, Ok), result
    assert result.value == []


def test_blockKey指定時の評価時型エラーはハードエラーとしてINVALID_JMESPATH_EXPRESSIONを返す():
    """blockKeyを明示指定した単一ブロック評価では、評価時型エラーもスキップせずハードエラーで返す
    （blockKey省略時の全ブロック評価とは異なる。ユーザーが明示指定したブロックに式が合わなかった
    ことをそのまま伝える）。"""
    compiled = _compile_jmespath("items[?contains(rule, 'CLI')]").value
    root = {"blockType": "X", "items": [{"title": "ruleフィールドを持たない要素"}]}
    result = _evaluate(compiled, root)
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_JMESPATH_EXPRESSION"

"""uc-check-query-precedes-array-fill の受け入れテスト（ネイティブpytest）。"""
from waffle.application.usecases.check_query_precedes_array_fill import CheckQueryPrecedesArrayFill
from waffle.shared.result import Ok


def _engine() -> CheckQueryPrecedesArrayFill:
    return CheckQueryPrecedesArrayFill()


def test_配列値を含むfillで先行queryが無い場合は拒否される():
    """
    Given targetPathが"X.json"であり、hasArrayValueがtrueである
    And queriedPathsに"X.json"が含まれていない
    When CheckQueryPrecedesArrayFillを実行する
    Then 拒否判定が返り、理由に先行queryが必要である旨が含まれる
    """
    result = _engine().run("X.json", True, [])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is False
    assert result.value["reason"]


def test_配列値を含むfillで先行queryがある場合は許可される():
    """
    Given targetPathが"X.json"であり、hasArrayValueがtrueである
    And queriedPathsに"X.json"が含まれている
    When CheckQueryPrecedesArrayFillを実行する
    Then 許可判定が返る
    """
    result = _engine().run("X.json", True, ["X.json"])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is True


def test_配列値を含まないfillは先行queryの有無に関わらず許可される():
    """
    Given hasArrayValueがfalseである
    And queriedPathsが空である
    When CheckQueryPrecedesArrayFillを実行する
    Then 許可判定が返る
    """
    result = _engine().run("X.json", False, [])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is True

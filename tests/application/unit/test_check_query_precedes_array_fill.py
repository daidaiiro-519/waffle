"""CheckQueryPrecedesArrayFillのユニットテスト（外部依存なしの判定ロジック）。"""
from waffle.application.usecases.check_query_precedes_array_fill import CheckQueryPrecedesArrayFill
from waffle.shared.result import Ok


def _engine() -> CheckQueryPrecedesArrayFill:
    return CheckQueryPrecedesArrayFill()


def test_配列値かつ先行queryが無ければ拒否する():
    result = _engine().run("x.json", True, [])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is False
    assert "x.json" in result.value["reason"]


def test_配列値かつ先行queryがあれば許可する():
    result = _engine().run("x.json", True, ["x.json"])
    assert isinstance(result, Ok)
    assert result.value == {"allowed": True, "reason": None}


def test_配列値でなければqueriedPathsに関わらず許可する():
    result = _engine().run("x.json", False, [])
    assert isinstance(result, Ok)
    assert result.value == {"allowed": True, "reason": None}


def test_queriedPathsに別のpathしか無ければ拒否する():
    result = _engine().run("x.json", True, ["y.json"])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is False

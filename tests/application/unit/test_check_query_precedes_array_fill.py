"""CheckQueryPrecedesArrayFillのユニットテスト（外部依存なしの判定ロジック）。"""
from waffle.application.usecases.check_query_precedes_array_fill import CheckQueryPrecedesArrayFill
from waffle.shared.result import Ok


def _engine() -> CheckQueryPrecedesArrayFill:
    return CheckQueryPrecedesArrayFill()


def test_array_value_without_preceding_query_is_rejected():
    """配列値かつ先行queryが無ければ拒否する。"""
    result = _engine().run("x.json", True, [])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is False
    assert "x.json" in result.value["reason"]


def test_array_value_with_preceding_query_is_allowed():
    """配列値かつ先行queryがあれば許可する。"""
    result = _engine().run("x.json", True, ["x.json"])
    assert isinstance(result, Ok)
    assert result.value == {"allowed": True, "reason": None}


def test_non_array_value_is_allowed_regardless_of_queried_paths():
    """配列値でなければqueriedPathsに関わらず許可する。"""
    result = _engine().run("x.json", False, [])
    assert isinstance(result, Ok)
    assert result.value == {"allowed": True, "reason": None}


def test_queried_paths_for_other_path_is_rejected():
    """queriedPathsに別のpathしか無ければ拒否する。"""
    result = _engine().run("x.json", True, ["y.json"])
    assert isinstance(result, Ok)
    assert result.value["allowed"] is False

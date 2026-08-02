"""PatchSchema の引数検査のテスト。

仕様のシナリオには対応しない、規約由来のテスト。
「application 境界は結果型（Result 等）で成否を返す」に従い、
形の違う引数を受け取っても例外を投げずに Err を返すことを確かめる。
"""
from waffle.application.usecases.patch_schema import PatchSchema
from waffle.shared.result import Err


class _Unused:
    """引数検査で弾かれるため、一度も呼ばれない port の偽実装。"""

    def load(self, ref: str) -> dict:
        raise AssertionError("引数検査より前に読んではいけない")


def _engine() -> PatchSchema:
    return PatchSchema(_Unused(), _Unused(), _Unused())


def test_run_rejects_non_mapping_params():
    """params が辞書でなければ INVALID_PARAM を返す（例外を投げない）。"""
    result = _engine().run("add_def", ["x"])
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_PARAM"


def test_create_version_rejects_non_mapping_params():
    """schemaRef を見ない create_version でも同じく弾く。"""
    result = _engine().run("create_version", ["x"])
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_PARAM"


def test_run_still_reports_missing_schema_ref():
    """辞書だが schemaRef が無い場合は従来どおり MISSING_PARAM を返す。"""
    result = _engine().run("add_def", {})
    assert isinstance(result, Err)
    assert result.details[0] == "MISSING_PARAM"

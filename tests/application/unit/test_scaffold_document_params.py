"""ScaffoldDocument の引数検査のテスト。

仕様のシナリオには対応しない、規約由来のテスト。
「application 境界は結果型（Result 等）で成否を返す」に従い、
形の違う引数を受け取っても例外を投げずに Err を返すことを確かめる。
"""
from waffle.application.usecases.scaffold_document import ScaffoldDocument
from waffle.shared.result import Err


class _UnusedDocs:
    """引数検査で弾かれるため、一度も呼ばれない DocumentRepository の偽実装。"""

    def load(self, path: str) -> dict:
        raise AssertionError("引数検査より前に document を読んではいけない")


class _UnusedSchemas:
    """同上。SchemaRepository の偽実装。"""

    def load(self, schema_ref: str) -> dict:
        raise AssertionError("引数検査より前に schema を読んではいけない")


def _engine() -> ScaffoldDocument:
    return ScaffoldDocument(_UnusedDocs(), _UnusedSchemas())


def test_fill_rejects_non_mapping_values():
    """values が辞書でなければ INVALID_PARAM を返す（例外を投げない）。"""
    result = _engine().run("fill", {"documentPath": "x.json", "values": [{"a": 1}]})
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_PARAM"


def test_fill_rejects_scalar_values():
    """values が文字列でも INVALID_PARAM を返す。"""
    result = _engine().run("fill", {"documentPath": "x.json", "values": "content.title"})
    assert isinstance(result, Err)
    assert result.details[0] == "INVALID_PARAM"


def test_fill_still_reports_missing_param():
    """values が無い場合は従来どおり MISSING_PARAM を返す。"""
    result = _engine().run("fill", {"documentPath": "x.json"})
    assert isinstance(result, Err)
    assert result.details[0] == "MISSING_PARAM"

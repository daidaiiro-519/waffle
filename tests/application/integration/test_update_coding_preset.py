"""uc-update-coding-preset の操作保証テスト（ネイティブpytest）。

プリセットと規約を特定し取得する解決プロセス自体の契約を、実物に対して確かめる。
"""
from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.update_coding_preset import UpdateCodingPreset
from waffle.shared.result import Err


def _engine() -> UpdateCodingPreset:
    return UpdateCodingPreset(FsDocumentRepository(), PackageCodingPresetRepository())


def test_unknown_preset_is_not_found():
    """
    Scenario: 存在しないプリセットはPRESET_NOT_FOUND
    When 存在しないプリセットを指定して反映する
    Then PRESET_NOT_FOUNDエラーが返る
    """
    result = _engine().run("存在しないプリセット", "architecture-waffle", ["rules"])
    assert isinstance(result, Err), result
    assert "PRESET_NOT_FOUND" in result.details


def test_unknown_source_document_is_invalid_path():
    """
    Scenario: 存在しない規約はINVALID_PATH
    When 存在しない規約を出どころに指定して反映する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run("python-hexagonal", "architecture-存在しない規約", ["rules"])
    assert isinstance(result, Err), result
    assert "INVALID_PATH" in result.details

"""CodingPresetRepository portの契約テスト。

仕様のシナリオには対応しない、規約由来のテスト。
書き込みを足したので、書いたものが読み戻せることを実物に対して確かめる。
"""
from pathlib import Path

import pytest

from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository

_TEMP = "test-contract-preset"
_PATH = Path("src/waffle/domain/model/CodingPresets") / (_TEMP + "." + "json")


def teardown_function():
    _PATH.unlink(missing_ok=True)


def _repository() -> PackageCodingPresetRepository:
    return PackageCodingPresetRepository()


def test_saved_preset_is_readable():
    """書き込んだプリセットが、そのまま読み戻せる。"""
    preset = {"architecture": {"rules": {"items": [{"level": "必須", "rule": "規約"}]}}}
    _repository().save(_TEMP, preset)
    assert _repository().load(_TEMP) == preset


def test_saved_preset_appears_in_the_listing():
    """書き込んだプリセットが一覧に現れる。"""
    _repository().save(_TEMP, {"architecture": {}})
    assert _TEMP in _repository().list_names()


def test_unknown_preset_raises_file_not_found():
    """存在しないプリセットの読み出しは FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        _repository().load("存在しないプリセット")


def test_saving_twice_keeps_the_latest():
    """同じ名前へ書き直すと、後の内容が残る。"""
    _repository().save(_TEMP, {"architecture": {"rules": {"items": []}}})
    _repository().save(_TEMP, {"architecture": {"rules": {"items": [{"rule": "後"}]}}})
    assert _repository().load(_TEMP)["architecture"]["rules"]["items"] == [{"rule": "後"}]

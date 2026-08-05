"""uc-init-coding-preset の操作保証テスト。

何度実行しても既に生成したものを変えないこと（冪等性）と、知らないプリセット名を
拒むこと。どちらも1回の実行の結果ではなく、実行を跨いだ約束なのでここに置く。
"""
from pathlib import Path

from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.init_coding_preset import InitCodingPreset
from waffle.shared.result import Err, Ok

_PRODUCT = "test-integration-init-preset"
_PATHS = [
    Path(f".waffle/documents/coding/{kind}-{_PRODUCT}.json")
    for kind in ("tech-stack", "architecture", "coding-standard", "test-standard")
]


def teardown_function():
    for p in _PATHS:
        p.unlink(missing_ok=True)


def _engine() -> InitCodingPreset:
    return InitCodingPreset(FsDocumentRepository(), PackageCodingPresetRepository())


def test_既に生成済みのdocumentは再initで変更されない():
    """
    Scenario: 既に生成済みのdocumentは再initで変更されない
    Given 既にinit済みの4document
    When 同じpresetName・productNameでinitを再実行する
    Then 既存の4documentは一切変更されない
    """
    engine = _engine()
    first = engine.run("python-hexagonal", _PRODUCT)
    assert isinstance(first, Ok), first
    before = [p.read_bytes() for p in _PATHS]

    second = engine.run("python-hexagonal", _PRODUCT)

    assert isinstance(second, Ok), second
    assert second.value["created"] == []
    assert sorted(second.value["skipped"]) == sorted(str(p) for p in _PATHS)
    assert [p.read_bytes() for p in _PATHS] == before


def test_存在しないプリセット名はPRESET_NOT_FOUND():
    """
    Scenario: 存在しないプリセット名はPRESET_NOT_FOUND
    Given 存在しないpresetName
    When initを実行する
    Then PRESET_NOT_FOUNDエラーが返る
    """
    result = _engine().run("no-such-preset", _PRODUCT)

    assert isinstance(result, Err)
    assert result.details == ["PRESET_NOT_FOUND"]

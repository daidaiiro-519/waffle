"""uc-init-coding-preset の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.init_coding_preset import InitCodingPreset
from waffle.shared.result import Err, Ok

_PRODUCT = "test-acceptance-init-preset"
_PATHS = [
    Path(f".waffle/documents/coding/{kind}-{_PRODUCT}.json")
    for kind in ("tech-stack", "architecture", "coding-standard", "test-standard")
]


def teardown_function():
    for p in _PATHS:
        p.unlink(missing_ok=True)


def _engine() -> InitCodingPreset:
    return InitCodingPreset(FsDocumentRepository(), PackageCodingPresetRepository())


def test_プリセットから4documentを一括生成する():
    """
    Given python-hexagonalプリセット
    When 新しいプロダクト名でinitする
    Then tech-stack/architecture/coding-standard/test-standardの4documentが生成される
    """
    result = _engine().run("python-hexagonal", _PRODUCT)
    assert isinstance(result, Ok), result
    assert sorted(result.value["created"]) == sorted(str(p) for p in _PATHS)
    assert result.value["skipped"] == []
    for p in _PATHS:
        assert p.is_file()
        doc = json.loads(p.read_text(encoding="utf-8"))
        assert doc["schemaRef"] == "CodingSchema/v3"
        assert doc["stack"] == "python-hexagonal"
        assert doc["status"] == "ACTIVE"
        assert doc["documentId"] in doc["content"]["title"]["title"]


def test_タイトルにプロダクト固有のdocumentIdが付与される():
    """
    Given python-hexagonalプリセット
    When 新しいプロダクト名でinitする
    Then 各documentのtitleは「説明句：documentId」の形式になる
    """
    result = _engine().run("python-hexagonal", _PRODUCT)
    assert isinstance(result, Ok), result
    tech_stack_path = Path(f".waffle/documents/coding/tech-stack-{_PRODUCT}.json")
    doc = json.loads(tech_stack_path.read_text(encoding="utf-8"))
    assert doc["content"]["title"]["title"] == f"Python/ヘキサゴナル構成の採用技術を定めるTech Stack仕様：tech-stack-{_PRODUCT}"


def test_既に存在するdocumentは上書きせずskipする():
    """
    Given 既にinit済みの4document
    When 同じプロダクト名で再度initする
    Then 何も上書きされずcreatedは空、skippedに4件とも含まれる
    """
    engine = _engine()
    first = engine.run("python-hexagonal", _PRODUCT)
    assert isinstance(first, Ok), first
    second = engine.run("python-hexagonal", _PRODUCT)
    assert isinstance(second, Ok), second
    assert second.value["created"] == []
    assert sorted(second.value["skipped"]) == sorted(str(p) for p in _PATHS)


def test_存在しないプリセット名はPRESET_NOT_FOUNDを返す():
    """
    Given 存在しないプリセット名
    When initする
    Then PRESET_NOT_FOUNDエラーになる
    """
    result = _engine().run("no-such-preset", _PRODUCT)
    assert isinstance(result, Err)
    assert result.details == ["PRESET_NOT_FOUND"]

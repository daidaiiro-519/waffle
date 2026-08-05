"""uc-init-coding-preset の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.init_coding_preset import InitCodingPreset
from waffle.shared.result import Ok

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


def test_creates_four_documents_from_preset():
    """
    Scenario: プリセットから4documentを一括生成する
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
        assert doc["schemaRef"] == "CodingSchema/v4"
        assert doc["stack"] == "python-hexagonal"
        assert doc["status"] == "ACTIVE"
        assert doc["documentId"] in doc["content"]["title"]["title"]


def test_title_carries_product_specific_document_id():
    """
    Scenario: タイトルにプロダクト固有のdocumentIdが付与される
    Given python-hexagonalプリセット
    When 新しいプロダクト名でinitする
    Then 各documentのtitleは「説明句：documentId」の形式になる
    """
    result = _engine().run("python-hexagonal", _PRODUCT)
    assert isinstance(result, Ok), result
    tech_stack_path = Path(f".waffle/documents/coding/tech-stack-{_PRODUCT}.json")
    doc = json.loads(tech_stack_path.read_text(encoding="utf-8"))
    assert doc["content"]["title"]["title"] == f"Python/ヘキサゴナル構成の採用技術を定めるTech Stack仕様：tech-stack-{_PRODUCT}"

"""uc-init-coding-preset の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.coding_preset_repo import PackageCodingPresetRepository
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.domain.services.schema_versioning import latest_version
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
    return InitCodingPreset(FsDocumentRepository(), PackageCodingPresetRepository(), PackageSchemaRepository())


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


def test_created_documents_point_at_the_latest_schema_version():
    """
    Scenario: プリセットから作る規約は最新の版を指す
    Given 規約のschemaに複数の版がある
    When プリセットからプロダクト固有の規約を作る
    Then 作られた規約はそのschemaの最新の版を指す
    """
    schemas = PackageSchemaRepository()
    versions = schemas.list_versions("CodingSchema")
    assert len(versions) > 1, versions
    expected = f"CodingSchema/{latest_version(versions)}"

    result = _engine().run("python-hexagonal", _PRODUCT)
    assert isinstance(result, Ok), result

    documents = FsDocumentRepository()
    for p in _PATHS:
        assert documents.load(str(p))["schemaRef"] == expected, p

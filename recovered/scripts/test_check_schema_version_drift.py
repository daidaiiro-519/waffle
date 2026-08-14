"""uc-check-schema-version-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_schema_version_drift import CheckSchemaVersionDrift
from waffle.shared.result import Err, Ok

from tests.fakes import FakeSchemaRepository


_EMPTY_SCHEMA = {"properties": {"content": {"type": "object", "properties": {}}}}


def _schema_repository(
    versions_by_name: dict[str, list[str]],
    schemas_by_ref: dict[str, dict] | None = None,
) -> FakeSchemaRepository:
    """存在する版の一覧から、共有の偽実装を組み立てる。

    共有の偽実装は list_versions を schemaRef の辞書から導出するため、
    「list_versions は知っているが load できない版」を作れない。
    明示されなかった版には空の schema を割り当てる。
    """
    given = schemas_by_ref or {}
    schemas = {
        f"{name}/{version}": given.get(f"{name}/{version}", _EMPTY_SCHEMA)
        for name, versions in versions_by_name.items()
        for version in versions
    }
    return FakeSchemaRepository({**schemas, **given})


def _engine(versions_by_name: dict[str, list[str]], schemas_by_ref: dict[str, dict] | None = None) -> CheckSchemaVersionDrift:
    return CheckSchemaVersionDrift(FsDocumentRepository(), _schema_repository(versions_by_name, schemas_by_ref))


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def test_aligned_tree_reports_empty_lists_and_aligned_verdict(tmp_path):
    """
    Scenario: 追従できていれば全て空で、判定も追従済みになる
    Given 全Documentが最新の版を指し、宣言済みの欄も揃っている置き場所
    When 版の追従を調べる
    Then 全ての一覧が空で、追従できているという判定が返る
    """
    _write(tmp_path / "doc-a.json", {"documentId": "doc-a", "schemaRef": "FooSchema/v2"})

    result = _engine({"FooSchema": ["v1", "v2"]}).run(str(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value == {
        "aligned": True,
        "broken_references": [],
        "outdated_references": [],
        "missing_declared_fields": [],
    }


def test_schema_ref_pointing_to_missing_version(tmp_path):
    """
    Scenario: 実在しない版を指す参照を見つける
    Given 実在しない版を指すDocument
    When 版の追従を調べる
    Then その組が指す先の無い参照として返り、追従できていないという判定が返る
    """
    _write(tmp_path / "doc-a.json", {"documentId": "doc-a", "schemaRef": "FooSchema/v9"})

    result = _engine({"FooSchema": ["v1", "v2"]}).run(str(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value["broken_references"] == [{"document": str(tmp_path / "doc-a.json"), "schemaRef": "FooSchema/v9"}]
    assert result.value["aligned"] is False


def test_document_referencing_outdated_version(tmp_path):
    """
    Scenario: 最新でない版を指す参照を見つける
    Given 最新でない版を指すDocument
    When 版の追従を調べる
    Then その組が追いついていない参照として返り、追従できていないという判定が返る
    """
    _write(tmp_path / "doc-a.json", {"documentId": "doc-a", "schemaRef": "FooSchema/v1"})

    result = _engine({"FooSchema": ["v1", "v2"]}).run(str(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value["outdated_references"] == [
        {"document": str(tmp_path / "doc-a.json"), "schemaRef": "FooSchema/v1", "latest": "FooSchema/v2"}
    ]
    assert result.value["aligned"] is False


def test_document_missing_declared_value_field(tmp_path):
    """
    Scenario: 宣言された欄を持たないDocumentを見つける
    Given Schemaが宣言する必須の欄を持たないDocument
    When 版の追従を調べる
    Then その組が追従していない欄として返り、追従できていないという判定が返る
    """
    schema = {
        "properties": {
            "content": {
                "type": "object",
                "required": ["note"],
                "properties": {
                    "note": {"type": "string", "x-prompt-write": "備考"},
                },
            }
        }
    }
    _write(tmp_path / "doc-a.json", {"documentId": "doc-a", "schemaRef": "FooSchema/v2", "content": {}})

    result = _engine({"FooSchema": ["v2"]}, {"FooSchema/v2": schema}).run(str(tmp_path))
    assert isinstance(result, Ok), result
    assert result.value["missing_declared_fields"] == [
        {"document": str(tmp_path / "doc-a.json"), "path": "content.note"}
    ]
    assert result.value["aligned"] is False


def test_missing_documents_root_is_invalid_path(tmp_path):
    """
    Scenario: 走査の対象が無ければINVALID_PATH
    Given 実在しない走査の対象
    When 版の追従を調べる
    Then INVALID_PATH エラーが返る
    """
    result = _engine({"FooSchema": ["v1"]}).run(str(tmp_path / "no-such-dir"))
    assert isinstance(result, Err), result
    assert result.details == ["INVALID_PATH"]

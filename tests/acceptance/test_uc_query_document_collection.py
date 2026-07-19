"""uc-query-document-collection の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.query_document_collection import QueryDocumentCollection
from waffle.shared.result import Err, Ok

_TARGET_DIR = ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase"


def _engine() -> QueryDocumentCollection:
    return QueryDocumentCollection(FsDocumentRepository(), PackageSchemaRepository())


def test_grep_documentsはディレクトリ横断でpatternに一致する値を収集する():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When operation grep_documents を pattern で実行する
    Then patternに一致した値がDocumentのpath単位でvalueとして返る
    """
    result = _engine().run("grep_documents", _TARGET_DIR, {"pattern": "resolve_ref"})
    assert isinstance(result, Ok), result
    matched_paths = result.value["value"].keys()
    assert any("uc-query-document.json" in p for p in matched_paths)


def test_filter_documentsはメタフィールドの一致でDocumentを絞り込む(tmp_path, monkeypatch):
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When operation filter_documents を key tags, value repo:has-udd で実行する
    Then tagsにrepo:has-uddを含むDocumentのpathとmetaがvalueとして返る
    """
    monkeypatch.chdir(tmp_path)  # grep_documents/filter_documentsもindex_scan_documentsと同じG7（プロジェクトルート閉じ込め）を持つため
    _write_doc(tmp_path / "a.json", "doc-a", tags=["repo:has-udd"])
    _write_doc(tmp_path / "b.json", "doc-b", tags=["repo:waffle"])

    result = _engine().run("filter_documents", str(tmp_path), {"key": "tags", "value": "repo:has-udd"})
    assert isinstance(result, Ok), result
    matched = result.value["value"]
    assert len(matched) == 1
    (path, meta), = matched.items()
    assert path.endswith("a.json")
    assert meta["documentId"] == "doc-a"


def test_index_scan_documentsはディレクトリ横断でindexとtagsを集約する():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When operation index_scan_documents を実行する
    Then ディレクトリ配下の各Documentのindexとtagsがまとめてvalueとして返り、promptには各要素のpromptを参照する案内が入る
    """
    result = _engine().run("index_scan_documents", _TARGET_DIR)
    assert isinstance(result, Ok), result
    entry = next(v for k, v in result.value["value"].items() if "uc-query-document.json" in k)
    assert "context:waffle" in entry["tags"]
    assert result.value["prompt"]
    assert entry["blocks"]["mainFlow"]["prompt"]


def test_一致するDocumentが無くても正常系で空を返す():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When 一致しないpatternでgrep_documentsを実行する
    Then valueは空であり、エラーにはならない
    """
    result = _engine().run("grep_documents", _TARGET_DIR, {"pattern": "存在しないはずの文字列xyz123"})
    assert isinstance(result, Ok), result
    assert result.value["value"] == {}


def test_未知のoperationはエラーを返す():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When 未知の operation を実行する
    Then INVALID_OPERATION エラーが返る
    """
    result = _engine().run("unknown_op", _TARGET_DIR, {})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_OPERATION"


def test_存在しないディレクトリはエラーを返す():
    """
    Given 実在しない対象ディレクトリ
    When 本usecaseを実行する
    Then INVALID_PATH エラーが返る
    """
    result = _engine().run("grep_documents", "does/not/exist", {"pattern": "x"})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_不正な正規表現はエラーを返す():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When 不正な正規表現で grep_documents を実行する
    Then INVALID_PATTERN エラーが返る
    """
    result = _engine().run("grep_documents", _TARGET_DIR, {"pattern": "("})
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATTERN"


def _write_doc(path, document_id: str, tags: list[str]) -> None:
    doc = {
        "documentId": document_id,
        "documentType": "Handoff",
        "schemaRef": "HandoffSchema/v1",
        "tags": tags,
        "content": {},
    }
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

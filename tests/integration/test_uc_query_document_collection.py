"""uc-query-document-collection のguaranteeScenarios(operationGuaranteesと対)に対応する統合テスト。"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.schema_repo import PackageSchemaRepository
from waffle.application.usecases.query_document_collection import QueryDocumentCollection
from waffle.shared.result import Ok

_TARGET_DIR = ".waffle/documents/specs/bc-waffle/subdomain/sd-document-management/usecase"


def _engine() -> QueryDocumentCollection:
    return QueryDocumentCollection(FsDocumentRepository(), PackageSchemaRepository())


def test_同一条件での再実行はべき等である():
    """
    Given QueryDocumentCollection システム と対象ディレクトリ
    When 同一のoperationとparamsを2回連続で実行する
    Then 2回の結果は完全に一致する
    """
    params = {"pattern": "resolve_ref"}
    first = _engine().run("grep_documents", _TARGET_DIR, params)
    second = _engine().run("grep_documents", _TARGET_DIR, params)
    assert isinstance(first, Ok), first
    assert isinstance(second, Ok), second
    assert first.value == second.value

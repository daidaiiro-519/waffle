"""uc-check-domain-service-drift のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(対象のdocuments_root)に対応する統合テスト。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_domain_service_drift import CheckDomainServiceDrift
from waffle.shared.result import Err


def _engine() -> CheckDomainServiceDrift:
    return CheckDomainServiceDrift(FsDocumentRepository())


def test_存在しないdocuments_rootはINVALID_PATH():
    """
    When 存在しないdocuments_rootでドリフト検査を実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run("does/not/exist", ".")
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

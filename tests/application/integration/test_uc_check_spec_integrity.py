"""uc-check-spec-integrity のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(対象のbc.json)に対応する統合テスト。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_spec_integrity import CheckSpecIntegrity
from waffle.shared.result import Err


def _engine() -> CheckSpecIntegrity:
    return CheckSpecIntegrity(FsDocumentRepository())


def test_missing_bc_json_is_invalid_path():
    """
    Scenario: 存在しないbc.jsonはINVALID_PATH
    When 存在しないbc.jsonのパスで参照整合性検査を実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run("does/not/exist.json", ".waffle/documents")
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

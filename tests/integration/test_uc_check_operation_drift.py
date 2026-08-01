"""uc-check-operation-drift のguaranteeScenarios(operationGuaranteesと対)に対応する統合テスト。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_operation_drift import CheckOperationDrift
from waffle.shared.result import Err


def _engine() -> CheckOperationDrift:
    return CheckOperationDrift(FsDocumentRepository())


def test_missing_documents_root_is_invalid_path(tmp_path):
    """
    Scenario: 存在しないdocuments_rootはINVALID_PATH
    When 存在しないdocuments_rootでoperationドリフト検査を実行する
    Then INVALID_PATHエラーが返る
    """
    from waffle.shared.result import Err

    src_root = tmp_path / "src"
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(tmp_path / "no-such-dir"), str(src_root))
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

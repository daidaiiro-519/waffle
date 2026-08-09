"""uc-check-aggregate-class-drift のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(対象のdocuments_root)に対応する統合テスト。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor
from waffle.application.usecases.check_aggregate_class_drift import CheckAggregateClassDrift
from waffle.shared.result import Err

from tests.fakes import JAVA_NAMING, PYTHON_NAMING


def _engine() -> CheckAggregateClassDrift:
    return CheckAggregateClassDrift(FsDocumentRepository(), TreeSitterClassExtractor())


def test_missing_documents_root_is_invalid_path():
    """
    Scenario: 存在しないdocuments_rootはINVALID_PATH
    When 存在しないdocuments_rootでクラス名ドリフト検査を実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run("does/not/exist", ".", PYTHON_NAMING)
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

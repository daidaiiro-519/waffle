"""uc-check-scenario-drift のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(対象のspec.json・テストファイル)に対応する統合テスト。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.shared.result import Err

from pathlib import Path as _Path

from tests.fakes import scenario_binding


def _tests_root(test_path) -> _Path:
    """テストは {root}/{層}/{種別}/x.py に置かれるので、木の根はその3つ上。"""
    return _Path(str(test_path)).parent.parent.parent

SPEC = ".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-scenario-drift.json"


def _engine() -> CheckScenarioDrift:
    return CheckScenarioDrift(FsDocumentRepository(), TreeSitterTestFunctionExtractor())


def test_missing_spec_is_invalid_path():
    """
    Scenario: 存在しないspec.jsonはINVALID_PATH
    When 存在しないspec.jsonのパスでドリフト検査を実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run(
        spec_path="does/not/exist.json",
        test_file_path="tests/application/integration/test_uc_check_scenario_drift.py")

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_missing_test_file_is_invalid_path():
    """
    Scenario: 存在しないテストファイルはINVALID_PATH
    When 存在しないテストファイルのパスでドリフト検査を実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run(spec_path=SPEC, test_file_path="does/not/exist.py",
                           binding=scenario_binding(_tests_root("does/not/exist.py")))

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

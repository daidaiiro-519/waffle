"""uc-lint-docstring のguaranteeScenarios(operationGuaranteesと対)のうち、
リポジトリ解決契約(対象パス)に対応する統合テスト。
"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.pydoclint_linter import PydoclintLinter
from waffle.adapters.outbound.python_ast_source_scanner import PythonAstSourceScanner
from waffle.application.usecases.lint_docstring import LintDocstring
from waffle.application.usecases.scan_source_code import ScanSourceCode
from waffle.shared.result import Err


def _engine() -> LintDocstring:
    scan_engine = ScanSourceCode(FsDocumentRepository(), PythonAstSourceScanner())
    return LintDocstring(scan_engine, PydoclintLinter())


def test_存在しないパスはINVALID_PATH():
    """
    Given 実在しない対象パス
    When 本usecaseを実行する
    Then INVALID_PATHエラーが返る
    """
    result = _engine().run("does/not/exist", "google")
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"

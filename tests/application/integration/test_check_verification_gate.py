"""uc-check-verification-gate のguaranteeScenarios(operationGuaranteesと対)に対応する統合テスト。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.shared.result import Ok

from pathlib import Path as _Path

from tests.fakes import scenario_binding

_GHERKIN_A = "Scenario: 何かが起きる\n  Given 前提\n  When 操作する\n  Then 結果になる"


def _engine() -> CheckVerificationGate:
    return CheckVerificationGate(FsDocumentRepository(), TreeSitterTestFunctionExtractor())


class _Gate:
    """規約の宣言を毎回渡すための薄い包み。

    どの拡張子がどの言語かはスタックが宣言する。テストもその宣言を与える。
    """

    def run(self, *args):
        return _engine().run(*args, binding=scenario_binding(_Path(str(args[1])).parent))


def test_repeated_run_is_idempotent(tmp_path):
    """
    Scenario: 同一入力での再実行はべき等である
    Given CheckVerificationGate システム と同一の入力
    When 2回連続で実行する
    Then 2回の結果は完全に一致する
    """
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({
        "documentId": "test-spec",
        "content": {"acceptanceScenarios": {"scenarios": [
            {"name": "何かが起きる", "gherkin": _GHERKIN_A, "category": "正常系", "viewpoint": "", "covers": ""}
        ]}},
    }, ensure_ascii=False), encoding="utf-8")

    test_dir = tmp_path / "tests" / "acceptance"
    test_dir.mkdir(parents=True)
    test_path = test_dir / "test_spec.py"
    test_path.write_text(
        'def test_something_happens():\n'
        '    """\n'
        '    Scenario: 何かが起きる\n'
        '    Given 前提\n'
        '    When 操作する\n'
        '    Then 結果になる\n'
        '    """\n',
        encoding="utf-8",
    )

    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps({"passed": ["test_something_happens"], "failed": []}), encoding="utf-8")

    first = _Gate().run(str(spec_path), str(test_path), str(results_path))
    second = _Gate().run(str(spec_path), str(test_path), str(results_path))

    assert isinstance(first, Ok), first
    assert isinstance(second, Ok), second
    assert first.value == second.value

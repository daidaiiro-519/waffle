"""uc-check-verification-gate の受け入れテスト（ネイティブpytest）。

実行結果が並べるのはテストの名前、specが持つのはシナリオ名で、両者は別の
語彙。この判定はその2つを対応表越しに突き合わせる。
"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.shared.result import Err, Ok

from pathlib import Path as _Path

from tests.fakes import scenario_binding

_GHERKIN_A = "Scenario: 何かが起きる\n  Given 前提\n  When 操作する\n  Then 結果になる"
_DOC_A = ('    """\n    Scenario: 何かが起きる\n'
          '    Given 前提\n    When 操作する\n    Then 結果になる\n    """\n')


def _engine() -> CheckVerificationGate:
    return CheckVerificationGate(FsDocumentRepository(), TreeSitterTestFunctionExtractor())


class _Gate:
    """規約の宣言を毎回渡すための薄い包み。

    どの拡張子がどの言語かはスタックが宣言する。テストもその宣言を与える。
    """

    def run(self, *args):
        return _engine().run(*args, binding=scenario_binding(_Path(str(args[1])).parent))


def _spec(tmp_path, scenarios):
    path = tmp_path / "spec.json"
    doc = {"documentId": "test-spec", "content": {"acceptanceScenarios": {"scenarios": scenarios}}}
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


def _scenario(name, gherkin):
    return {"name": name, "gherkin": gherkin, "category": "正常系", "viewpoint": "", "covers": ""}


def _test_file(tmp_path, body):
    test_dir = tmp_path / "tests" / "acceptance"
    test_dir.mkdir(parents=True, exist_ok=True)
    path = test_dir / "test_spec.py"
    path.write_text(body, encoding="utf-8")
    return path


def _paired_test(tmp_path):
    """シナリオ「何かが起きる」に対応する、名前の異なるテスト。"""
    return _test_file(tmp_path, "def test_something_happens():\n" + _DOC_A)


def _results(tmp_path, passed=None, failed=None):
    path = tmp_path / "results.json"
    path.write_text(json.dumps({"passed": passed or [], "failed": failed or []},
                               ensure_ascii=False), encoding="utf-8")
    return path


def test_missing_scenario_blocks(tmp_path):
    """
    Scenario: 未実装のシナリオがあるときはblockedを返す
    Given specのacceptanceScenariosに対して未実装のシナリオを1件含む対象
    When CheckVerificationGateを実行する
    Then statusはblockedであり、reasonsに未実装のシナリオが含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    result = _Gate().run(str(spec_path), str(_test_file(tmp_path, "")),
                           str(_results(tmp_path)))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"
    assert any("何かが起きる" in reason for reason in result.value["reasons"])


def test_unexplained_drift_needs_human(tmp_path):
    """
    Scenario: 意図不明なズレがあるときはneeds_humanを返す
    Given specに無いテスト（orphaned_in_tests）を1件含む対象
    When CheckVerificationGateを実行する
    Then statusはneeds_humanであり、reasonsにそのズレが含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(tmp_path,
                           "def test_something_happens():\n" + _DOC_A
                           + "\n\ndef test_orphaned():\n    pass\n")
    results_path = _results(tmp_path, passed=["test_something_happens"])

    result = _Gate().run(str(spec_path), str(test_path), str(results_path))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "needs_human"
    assert any("test_orphaned" in reason for reason in result.value["reasons"])


def test_failed_test_blocks(tmp_path):
    """
    Scenario: 対応関係に差分は無いがテストが失敗しているときはblockedを返す
    Given spec⇄テストの対応関係に差分が無く、1件failedを含むテスト実行結果
    When CheckVerificationGateを実行する
    Then statusはblockedであり、reasonsに失敗したテスト名が含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    results_path = _results(tmp_path, failed=["test_something_happens"])

    result = _Gate().run(str(spec_path), str(_paired_test(tmp_path)), str(results_path))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"
    assert any("何かが起きる" in reason for reason in result.value["reasons"])


def test_all_passed_is_ready(tmp_path):
    """
    Scenario: 対応関係に差分が無く全テストが成功しているときはreadyを返す
    Given spec⇄テストの対応関係に差分が無く、全てpassedのテスト実行結果
    When CheckVerificationGateを実行する
    Then statusはreadyである
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    results_path = _results(tmp_path, passed=["test_something_happens"])

    result = _Gate().run(str(spec_path), str(_paired_test(tmp_path)), str(results_path))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "ready"


def test_priority_gives_single_status(tmp_path):
    """
    Scenario: 複数条件に該当するときは優先順位に従い単一のstatusを返す
    Given missing_in_testsとorphaned_in_testsを同時に含む対象
    When CheckVerificationGateを実行する
    Then statusはblockedである（missing_in_testsが最優先）
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(tmp_path, "def test_orphaned():\n    pass\n")

    result = _Gate().run(str(spec_path), str(test_path), str(_results(tmp_path)))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"


def test_failed_matched_by_test_name(tmp_path):
    """
    Scenario: 落ちたテストはテスト名で突き合わせて検出する
    Given 対応関係に差分が無く、シナリオ名とは異なる名前のテストが1件failedである実行結果
    When 検証ゲートの判定を実行する
    Then status blocked が返る
    And reasonsにそのシナリオ名が含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    results_path = _results(tmp_path, failed=["test_something_happens"])

    result = _Gate().run(str(spec_path), str(_paired_test(tmp_path)), str(results_path))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"
    assert result.value["reasons"] == ["failed: 何かが起きる"]


def test_unknown_identifier_does_not_yield_ready(tmp_path):
    """
    Scenario: 実行結果の識別子が対応表と噛み合わないときreadyを返さない
    Given 対応関係に差分が無く、failedにどの対のテスト名とも一致しない識別子だけが並ぶ実行結果
    When 検証ゲートの判定を実行する
    Then status ready は返らない
    And reasonsに識別子の不整合が含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    results_path = _results(tmp_path, failed=["何かが起きる"])

    result = _Gate().run(str(spec_path), str(_paired_test(tmp_path)), str(results_path))

    assert isinstance(result, Ok), result
    assert result.value["status"] != "ready"
    assert any("unknown_test_identifier" in reason for reason in result.value["reasons"])


def test_duplicate_declarations_need_human(tmp_path):
    """
    Scenario: 同じ宣言行を複数のテストが名乗っているときneeds_humanを返す
    Given 同一の宣言行を2件のテストが名乗っている状態
    When 検証ゲートの判定を実行する
    Then status needs_human が返る
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(tmp_path,
                           "def test_first():\n" + _DOC_A + "\n\ndef test_copied():\n" + _DOC_A)

    result = _Gate().run(str(spec_path), str(test_path), str(_results(tmp_path)))

    assert isinstance(result, Ok), result
    assert result.value["status"] == "needs_human"


def test_missing_spec_path_errors(tmp_path):
    """
    Scenario: 存在しないspecPathはエラーを返す
    Given 実在しないspecPath
    When CheckVerificationGateを実行する
    Then INVALID_PATH エラーが返る
    """
    result = _Gate().run("does/not/exist.json", str(_test_file(tmp_path, "")),
                           str(_results(tmp_path)))

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_missing_test_file_path_errors(tmp_path):
    """
    Scenario: 存在しないtestFilePathはエラーを返す
    Given 実在しないtestFilePath
    When CheckVerificationGateを実行する
    Then INVALID_PATH エラーが返る
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    missing = tmp_path / "tests" / "acceptance" / "no_such_test.py"

    result = _Gate().run(str(spec_path), str(missing), str(_results(tmp_path)))

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_invalid_results_path_errors(tmp_path):
    """
    Scenario: 不正なtestResultsPathはエラーを返す
    Given 存在しない、またはJSONとして不正なtestResultsPath
    When CheckVerificationGateを実行する
    Then INVALID_TEST_RESULTS エラーが返る
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])

    result = _Gate().run(str(spec_path), str(_paired_test(tmp_path)),
                           str(tmp_path / "no_such_results.json"))

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_TEST_RESULTS"

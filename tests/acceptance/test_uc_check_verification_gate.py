"""uc-check-verification-gate の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_verification_gate import CheckVerificationGate
from waffle.shared.result import Err, Ok

_GHERKIN_A = "Scenario: 何かが起きる\n  Given 前提\n  When 操作する\n  Then 結果になる"


def _engine() -> CheckVerificationGate:
    return CheckVerificationGate(FsDocumentRepository())


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


def _results(tmp_path, passed=None, failed=None):
    path = tmp_path / "results.json"
    path.write_text(json.dumps({"passed": passed or [], "failed": failed or []}, ensure_ascii=False), encoding="utf-8")
    return path


def test_未実装のシナリオがあるときはblockedを返す(tmp_path):
    """
    Given specのacceptanceScenariosに対して未実装のシナリオを1件含む対象
    When CheckVerificationGateを実行する
    Then statusはblockedであり、reasonsに未実装のシナリオが含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(tmp_path, "")
    results_path = _results(tmp_path)

    result = _engine().run(str(spec_path), str(test_path), str(results_path))
    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"
    assert any("test_何かが起きる" in r for r in result.value["reasons"])


def test_意図不明なズレがあるときはneeds_humanを返す(tmp_path):
    """
    Given specに無いテスト（orphaned_in_tests）を1件含む対象
    When CheckVerificationGateを実行する
    Then statusはneeds_humanであり、reasonsにそのズレが含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(
        tmp_path,
        'def test_何かが起きる():\n'
        '    """\n'
        '    Given 前提\n'
        '    When 操作する\n'
        '    Then 結果になる\n'
        '    """\n'
        '    pass\n\n\n'
        'def test_孤立している():\n'
        '    pass\n',
    )
    results_path = _results(tmp_path, passed=["test_何かが起きる"])

    result = _engine().run(str(spec_path), str(test_path), str(results_path))
    assert isinstance(result, Ok), result
    assert result.value["status"] == "needs_human"
    assert any("test_孤立している" in r for r in result.value["reasons"])


def test_対応関係に差分は無いがテストが失敗しているときはblockedを返す(tmp_path):
    """
    Given spec⇄テストの対応関係に差分が無く、1件failedを含むテスト実行結果
    When CheckVerificationGateを実行する
    Then statusはblockedであり、reasonsに失敗したテスト名が含まれる
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(
        tmp_path,
        'def test_何かが起きる():\n'
        '    """\n'
        '    Given 前提\n'
        '    When 操作する\n'
        '    Then 結果になる\n'
        '    """\n'
        '    pass\n',
    )
    results_path = _results(tmp_path, failed=["test_何かが起きる"])

    result = _engine().run(str(spec_path), str(test_path), str(results_path))
    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"
    assert any("test_何かが起きる" in r for r in result.value["reasons"])


def test_対応関係に差分が無く全テストが成功しているときはreadyを返す(tmp_path):
    """
    Given spec⇄テストの対応関係に差分が無く、全てpassedのテスト実行結果
    When CheckVerificationGateを実行する
    Then statusはreadyである
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(
        tmp_path,
        'def test_何かが起きる():\n'
        '    """\n'
        '    Given 前提\n'
        '    When 操作する\n'
        '    Then 結果になる\n'
        '    """\n'
        '    pass\n',
    )
    results_path = _results(tmp_path, passed=["test_何かが起きる"])

    result = _engine().run(str(spec_path), str(test_path), str(results_path))
    assert isinstance(result, Ok), result
    assert result.value["status"] == "ready"


def test_複数条件に該当するときは優先順位に従い単一のstatusを返す(tmp_path):
    """
    Given missing_in_testsとorphaned_in_testsを同時に含む対象
    When CheckVerificationGateを実行する
    Then statusはblockedである（missing_in_testsが最優先）
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(tmp_path, 'def test_孤立している():\n    pass\n')
    results_path = _results(tmp_path)

    result = _engine().run(str(spec_path), str(test_path), str(results_path))
    assert isinstance(result, Ok), result
    assert result.value["status"] == "blocked"


def test_存在しないspecPathはエラーを返す(tmp_path):
    """
    Given 実在しないspecPath
    When CheckVerificationGateを実行する
    Then INVALID_PATH エラーが返る
    """
    test_path = _test_file(tmp_path, "")
    results_path = _results(tmp_path)

    result = _engine().run("does/not/exist.json", str(test_path), str(results_path))
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_存在しないtestFilePathはエラーを返す(tmp_path):
    """
    Given 実在しないtestFilePath
    When CheckVerificationGateを実行する
    Then INVALID_PATH エラーが返る
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    results_path = _results(tmp_path)
    missing_test_path = tmp_path / "tests" / "acceptance" / "no_such_test.py"

    result = _engine().run(str(spec_path), str(missing_test_path), str(results_path))
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_PATH"


def test_不正なtestResultsPathはエラーを返す(tmp_path):
    """
    Given 存在しない、またはJSONとして不正なtestResultsPath
    When CheckVerificationGateを実行する
    Then INVALID_TEST_RESULTS エラーが返る
    """
    spec_path = _spec(tmp_path, [_scenario("何かが起きる", _GHERKIN_A)])
    test_path = _test_file(
        tmp_path,
        'def test_何かが起きる():\n'
        '    """\n'
        '    Given 前提\n'
        '    When 操作する\n'
        '    Then 結果になる\n'
        '    """\n'
        '    pass\n',
    )

    result = _engine().run(str(spec_path), str(test_path), str(tmp_path / "no_such_results.json"))
    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_TEST_RESULTS"

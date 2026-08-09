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


def _spec_tree(tmp_path):
    """シナリオを1つ宣言する仕様を1件だけ持つ木を作る。"""
    import json
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "uc-sample.json").write_text(json.dumps({
        "documentId": "uc-sample",
        "content": {"acceptanceScenarios": {"scenarios": [
            {"name": "何かが起きる", "gherkin": "Scenario: 何かが起きる\n  When 実行する\n  Then 起きる"}]}},
    }, ensure_ascii=False), encoding="utf-8")
    return docs


def test_test_file_name_is_built_from_the_declaration(tmp_path):
    """
    Scenario: テストファイルの名前を規約の宣言から組み立てる
    Given 落とす接頭辞・前置・表記・中置・末尾を宣言している規約
    And その宣言どおりの名前を持つテストファイル
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then そのテストファイルが突き合わせの相手として見つかる
    """
    docs = _spec_tree(tmp_path)
    tests_root = tmp_path / "t"
    placed = tests_root / "application" / "acceptance"
    placed.mkdir(parents=True)
    (placed / "test_uc_sample.py").write_text(
        '"""\nScenario: 何かが起きる\n  When 実行する\n  Then 起きる\n"""\n'
        "def test_something():\n    pass\n", encoding="utf-8")

    result = _engine().run(documents_root=str(docs), tests_root=str(tests_root),
                           binding=scenario_binding(tests_root))

    assert result.value["missing_test_file"] == [], result.value
    assert [r["testPath"] for r in result.value["results"]] == [str(placed / "test_uc_sample.py")]


def test_changing_the_declaration_changes_where_it_looks(tmp_path):
    """
    Scenario: 名前の宣言を変えると探す先も変わる
    Given 前置を別の値へ変更した規約
    And 変更前の宣言で組み立てた名前のテストファイル
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then そのシナリオブロックがmissing_test_fileに含まれる
    """
    docs = _spec_tree(tmp_path)
    tests_root = tmp_path / "t"
    placed = tests_root / "application" / "acceptance"
    placed.mkdir(parents=True)
    (placed / "test_uc_sample.py").write_text(
        '"""\nScenario: 何かが起きる\n"""\ndef test_something():\n    pass\n', encoding="utf-8")

    binding = scenario_binding(tests_root)
    binding["testFileNaming"] = {**binding["testFileNaming"], "prefix": "spec_"}

    result = _engine().run(documents_root=str(docs), tests_root=str(tests_root),
                           binding=binding)

    assert [x["documentId"] for x in result.value["missing_test_file"]] == ["uc-sample"]
    assert result.value["missing_test_file"][0]["expectedPath"].endswith("spec_uc_sample.py")


def test_missing_naming_declaration_is_rejected(tmp_path):
    """
    Scenario: 名前を組み立てる宣言が無ければMISSING_DECLARATION
    Given テストファイルの名前の組み立て方を宣言していない規約
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then MISSING_DECLARATIONエラーが返る
    And 欠けた宣言を空とみなして検査を続けない
    """
    docs = _spec_tree(tmp_path)
    tests_root = tmp_path / "t"
    binding = scenario_binding(tests_root)
    del binding["testFileNaming"]["prefix"]

    result = _engine().run(documents_root=str(docs), tests_root=str(tests_root),
                           binding=binding)

    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_DECLARATION"
    assert "prefix" in result.message


def test_unplaced_scenario_block_is_reported(tmp_path):
    """
    Scenario: 置き場所が宣言されていない種別はmissing_placementに現れる
    Given あるシナリオ種別に対応する置き場所を宣言していない規約
    And その種別のシナリオを宣言しているspec
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then missing_placementにその種別が含まれる
    And その種別を黙って対象から外さない
    """
    docs = _spec_tree(tmp_path)
    tests_root = tmp_path / "t"
    binding = scenario_binding(tests_root)
    del binding["placements"][("application", "acceptance")]

    result = _engine().run(documents_root=str(docs), tests_root=str(tests_root),
                           binding=binding)

    assert result.value["missing_placement"] == [
        {"block": "acceptanceScenarios", "scenarioCount": 1}], result.value
    assert result.value["missing_test_file"] == []

"""uc-check-scenario-drift の受け入れテスト（ネイティブpytest）。

突き合わせのキーは、テストの文書コメント先頭に置いた宣言行
「Scenario: {シナリオ名}」。テストの名前は突き合わせに使わないため、
このファイル自身の関数名も対象言語の慣習どおりのASCIIで書く。
"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.shared.result import Err, Ok

from tests.fakes import scenario_binding

GHERKIN_BODY = "  Given 前提\n  When 操作する\n  Then 結果になる"
DOC_BODY = "    Given 前提\n    When 操作する\n    Then 結果になる"


def _engine() -> CheckScenarioDrift:
    return CheckScenarioDrift(FsDocumentRepository(), TreeSitterTestFunctionExtractor())


def _scenario(name: str, gherkin: str | None = None) -> dict:
    return {
        "name": name,
        "gherkin": gherkin if gherkin is not None else f"Scenario: {name}\n{GHERKIN_BODY}",
        "category": "正常系", "viewpoint": "", "covers": "",
    }


def _spec(directory: Path, *scenarios: dict, block: str = "acceptanceScenarios",
          document_id: str = "test-spec", name: str = "spec.json") -> Path:
    path = directory / name
    path.write_text(json.dumps({
        "documentId": document_id,
        "content": {block: {"scenarios": list(scenarios)}},
    }, ensure_ascii=False), encoding="utf-8")
    return path


def _spec_with_two_blocks(directory: Path) -> Path:
    path = directory / "spec.json"
    path.write_text(json.dumps({
        "documentId": "test-spec",
        "content": {
            "acceptanceScenarios": {"scenarios": [_scenario("受け入れ観点で起きる")]},
            "guaranteeScenarios": {"scenarios": [_scenario("保証観点で起きる")]},
        },
    }, ensure_ascii=False), encoding="utf-8")
    return path


def _test_file(directory: Path, source: str, name: str = "test_something.py") -> Path:
    path = directory / name
    path.write_text(source, encoding="utf-8")
    return path


def _py(*declarations: tuple[str, str]) -> str:
    """(テスト名, シナリオ名) から、宣言行つきのPythonのテストを組み立てる。"""
    return "\n\n".join(
        f'def {test_name}():\n    """\n    Scenario: {scenario}\n{DOC_BODY}\n    """\n'
        for test_name, scenario in declarations)


def _run(spec_path: Path, test_path: Path) -> dict:
    # テストは {tests_root}/{層}/{種別}/test_x.py に置かれるので、木の根はその3つ上
    result = _engine().run(spec_path=str(spec_path), test_file_path=str(test_path),
                           binding=scenario_binding(test_path.parent.parent.parent))
    assert isinstance(result, Ok), result
    return result.value


# ── 対応が取れている場合 ────────────────────────────────

def test_all_declared_scenarios_paired(tmp_path):
    """
    Scenario: 宣言行が揃っていれば対応していると判定する
    Given 宣言する全シナリオの宣言行を持ち、gherkinも転記されたテストファイル
    When ドリフト検査を実行する
    Then missing_in_tests・orphaned_in_tests・gherkin_mismatches・duplicate_declarations・spec_declaration_mismatchesが全て空で返る
    And matchedにシナリオ名とテスト名の対が含まれる
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, _py(("test_something_happens", "何かが起きる")))

    got = _run(spec_path, test_path)

    assert got["missing_in_tests"] == []
    assert got["orphaned_in_tests"] == []
    assert got["gherkin_mismatches"] == []
    assert got["duplicate_declarations"] == []
    assert got["spec_declaration_mismatches"] == []
    assert got["matched"] == [{"scenarioName": "何かが起きる", "testName": "test_something_happens"}]


def test_test_name_may_differ_from_scenario_name(tmp_path):
    """
    Scenario: テストの名前がシナリオ名と違っても対応づく
    Given シナリオ名と全く異なる名前を持ち、宣言行だけが一致するテスト
    When ドリフト検査を実行する
    Then そのシナリオはmatchedに含まれる
    And missing_in_testsにもorphaned_in_testsにも現れない
    """
    spec_path = _spec(tmp_path, _scenario("公開を止めると開けなくなる"))
    test_path = _test_file(tmp_path, _py(("test_zzz_unrelated_name", "公開を止めると開けなくなる")))

    got = _run(spec_path, test_path)

    assert [m["scenarioName"] for m in got["matched"]] == ["公開を止めると開けなくなる"]
    assert got["missing_in_tests"] == []
    assert got["orphaned_in_tests"] == []


# ── 対応が取れていない場合 ──────────────────────────────

def test_scenario_without_test_is_missing(tmp_path):
    """
    Scenario: 宣言されたシナリオに対応するテストが無いことを検出する
    Given シナリオを宣言するが、その宣言行を持つテストが無いテストファイル
    When ドリフト検査を実行する
    Then missing_in_testsにそのシナリオ名が含まれる
    """
    spec_path = _spec(tmp_path, _scenario("誰も書いていない"))
    test_path = _test_file(tmp_path, "def test_unrelated():\n    pass\n")

    assert _run(spec_path, test_path)["missing_in_tests"] == ["誰も書いていない"]


def test_test_without_declaration_is_orphaned(tmp_path):
    """
    Scenario: 宣言行を持たないテストを孤立として検出する
    Given 文書コメントが無い、または宣言行を持たないテストを含むテストファイル
    When ドリフト検査を実行する
    Then orphaned_in_testsにそのテストの名前が含まれる
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(
        tmp_path,
        _py(("test_something_happens", "何かが起きる"))
        + '\n\ndef test_no_declaration():\n    """宣言行を持たない補助的なテスト。"""\n')

    assert _run(spec_path, test_path)["orphaned_in_tests"] == ["test_no_declaration"]


def test_multiple_tests_without_declaration_all_listed(tmp_path):
    """
    Scenario: 宣言行を持たないテストが複数あっても全件が孤立として並ぶ
    Given 宣言行を持たないテストを2件含むテストファイル
    When ドリフト検査を実行する
    Then orphaned_in_testsに2件とも含まれる
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path,
                           "def test_first_without():\n    pass\n\n\n"
                           "def test_second_without():\n    pass\n")

    assert _run(spec_path, test_path)["orphaned_in_tests"] == [
        "test_first_without", "test_second_without"]


def test_renaming_scenario_shows_as_missing_and_orphaned(tmp_path):
    """
    Scenario: シナリオ名だけを変えたときは未実装と孤立の両方で現れる
    Given specのシナリオ名を変更し、テスト側の宣言行を変更していない状態
    When ドリフト検査を実行する
    Then missing_in_testsに新しいシナリオ名が含まれる
    And orphaned_in_testsにそのテストの名前が含まれる
    And gherkin_mismatchesには含まれない
    """
    spec_path = _spec(tmp_path, _scenario("新しい名前"))
    test_path = _test_file(tmp_path, _py(("test_something", "古い名前")))

    got = _run(spec_path, test_path)

    assert got["missing_in_tests"] == ["新しい名前"]
    assert got["orphaned_in_tests"] == ["test_something"]
    assert got["gherkin_mismatches"] == []


def test_changing_gherkin_only_shows_as_mismatch(tmp_path):
    """
    Scenario: gherkin本文だけを変えたときは文言不一致として現れる
    Given specのgherkinのGiven/When/Thenを変更し、宣言行は変更していない状態
    When ドリフト検査を実行する
    Then gherkin_mismatchesにそのシナリオ名が含まれる
    And missing_in_testsには含まれない
    """
    spec_path = _spec(tmp_path, _scenario(
        "何かが起きる", "Scenario: 何かが起きる\n  Given 変わった前提\n  When 操作する\n  Then 結果になる"))
    test_path = _test_file(tmp_path, _py(("test_something", "何かが起きる")))

    got = _run(spec_path, test_path)

    assert got["gherkin_mismatches"] == ["何かが起きる"]
    assert got["missing_in_tests"] == []


def test_identical_gherkin_distinguished_by_declaration(tmp_path):
    """
    Scenario: 本文が同一の2シナリオを宣言行で区別する
    Given Given/When/Thenが完全に同一で、名前だけが異なる2つのシナリオ
    And それぞれに対応する宣言行を持つ2つのテスト
    When ドリフト検査を実行する
    Then 2つのシナリオがそれぞれ正しいテストとmatchedになる
    """
    spec_path = _spec(tmp_path, _scenario("一つ目"), _scenario("二つ目"))
    test_path = _test_file(tmp_path, _py(("test_first", "一つ目"), ("test_second", "二つ目")))

    assert _run(spec_path, test_path)["matched"] == [
        {"scenarioName": "一つ目", "testName": "test_first"},
        {"scenarioName": "二つ目", "testName": "test_second"},
    ]


def test_duplicate_declarations_reported(tmp_path):
    """
    Scenario: 同じ宣言行を名乗るテストが2件あれば重複として報告する
    Given 同一の宣言行を持つテストを2件含むテストファイル
    When ドリフト検査を実行する
    Then duplicate_declarationsにその宣言行が含まれる
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, _py(("test_first", "何かが起きる"),
                                         ("test_copied", "何かが起きる")))

    assert _run(spec_path, test_path)["duplicate_declarations"] == ["Scenario: 何かが起きる"]


def test_spec_internal_declaration_mismatch_reported(tmp_path):
    """
    Scenario: spec自身の宣言行が名前と食い違えば報告する
    Given シナリオの名前と、gherkin先頭の宣言行が異なるspec
    When ドリフト検査を実行する
    Then spec_declaration_mismatchesにそのシナリオ名が含まれる
    """
    spec_path = _spec(tmp_path, _scenario(
        "正しい名前", "Scenario: 食い違った見出し\n" + GHERKIN_BODY))
    test_path = _test_file(tmp_path, "def test_unrelated():\n    pass\n")

    assert _run(spec_path, test_path)["spec_declaration_mismatches"] == ["正しい名前"]


# ── 書き方の揺れ ────────────────────────────────────────

def test_declaration_after_free_text_is_read(tmp_path):
    """
    Scenario: 文書コメントの飾りを落としてから宣言行を読む
    Given 対象言語の文書コメント記法で宣言行を書いたテスト
    When ドリフト検査を実行する
    Then その宣言行がシナリオと対応づく
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path,
                           'def test_something():\n'
                           '    """公開の停止を確かめる。\n\n'
                           '    Scenario: 何かが起きる\n' + DOC_BODY + '\n    """\n')

    assert [m["scenarioName"] for m in _run(spec_path, test_path)["matched"]] == ["何かが起きる"]


def test_leading_comment_language_pairs_correctly(tmp_path):
    """
    Scenario: 文書コメントが関数の直前に置かれる言語でも対応づく
    Given 文書コメントを関数の直前に置く言語のテストファイル
    And 宣言行を持つテストと持たないテストが並んでいる
    When ドリフト検査を実行する
    Then 宣言行を持つテストだけがmatchedになる
    And 直前のコメントが後続の別のテストへ取り違えられない
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, """
/**
 * Scenario: 何かが起きる
 * Given 前提
 * When 操作する
 * Then 結果になる
 */
test('something happens', () => {});

test('no declaration', () => {});
""", name="drift.test.js")

    got = _run(spec_path, test_path)

    assert got["matched"] == [{"scenarioName": "何かが起きる", "testName": "something happens"}]
    assert got["orphaned_in_tests"] == ["no declaration"]


# ── 層ごとの絞り込み ────────────────────────────────────

def test_acceptance_layer_targets_acceptance_scenarios_only(tmp_path):
    """
    Scenario: 受け入れの層のテストは受け入れシナリオだけを対象にする
    Given 受け入れシナリオと保証シナリオの両方を宣言するspec
    And 受け入れの層に配置され、受け入れシナリオだけを実装したテストファイル
    When ドリフト検査を実行する
    Then 保証シナリオはmissing_in_testsに含まれない
    """
    spec_path = _spec_with_two_blocks(tmp_path)
    test_dir = tmp_path / "tests" / "application" / "acceptance"
    test_dir.mkdir(parents=True)
    test_path = _test_file(test_dir, _py(("test_accepted", "受け入れ観点で起きる")), name="test_spec.py")

    got = _run(spec_path, test_path)

    assert got["missing_in_tests"] == []
    assert [m["scenarioName"] for m in got["matched"]] == ["受け入れ観点で起きる"]


def test_integration_layer_targets_guarantee_scenarios_only(tmp_path):
    """
    Scenario: 統合の層のテストは保証シナリオだけを対象にする
    Given 受け入れシナリオと保証シナリオの両方を宣言するspec
    And 統合の層に配置され、保証シナリオだけを実装したテストファイル
    When ドリフト検査を実行する
    Then 受け入れシナリオはmissing_in_testsに含まれない
    """
    spec_path = _spec_with_two_blocks(tmp_path)
    test_dir = tmp_path / "tests" / "application" / "integration"
    test_dir.mkdir(parents=True)
    test_path = _test_file(test_dir, _py(("test_guaranteed", "保証観点で起きる")), name="test_spec.py")

    got = _run(spec_path, test_path)

    assert got["missing_in_tests"] == []
    assert [m["scenarioName"] for m in got["matched"]] == ["保証観点で起きる"]


def test_unknown_layer_targets_every_block(tmp_path):
    """
    Scenario: 既知の配置に当てはまらないパスは全種を対象にする
    Given 受け入れシナリオと保証シナリオの両方を宣言するspec
    And いずれの層の配置にも当てはまらないテストファイル
    When ドリフト検査を実行する
    Then 保証シナリオがmissing_in_testsに含まれる
    """
    spec_path = _spec_with_two_blocks(tmp_path)
    test_path = _test_file(tmp_path, _py(("test_accepted", "受け入れ観点で起きる")), name="test_spec.py")

    assert _run(spec_path, test_path)["missing_in_tests"] == ["保証観点で起きる"]


# ── 退化とエラー ────────────────────────────────────────

def test_empty_spec_and_empty_test_file(tmp_path):
    """
    Scenario: シナリオが無いspecと、テストが無いファイルは空の判定になる
    Given シナリオを1件も宣言しないspecと、テストを1件も含まないファイル
    When ドリフト検査を実行する
    Then 全てのカテゴリが空で返る
    And エラーにならない
    """
    spec_path = _spec(tmp_path)
    test_path = _test_file(tmp_path, "x = 1\n")

    got = _run(spec_path, test_path)

    assert all(got[key] == [] for key in (
        "missing_in_tests", "orphaned_in_tests", "matched",
        "gherkin_mismatches", "duplicate_declarations", "spec_declaration_mismatches"))


def test_unparsable_test_file_is_invalid_source(tmp_path):
    """
    Scenario: 構文解析できないテストファイルはINVALID_SOURCE
    Given 構文が壊れているテストファイル
    When ドリフト検査を実行する
    Then INVALID_SOURCEエラーが返る
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, "def test_broken(:\n", name="test_broken.py")

    result = _engine().run(spec_path=str(spec_path), test_file_path=str(test_path),
                           binding=scenario_binding(test_path.parent.parent.parent))

    assert isinstance(result, Err), result
    assert result.details[0] == "INVALID_SOURCE"


def test_unsupported_language_is_rejected(tmp_path):
    """
    Scenario: 対応する言語が無ければUNSUPPORTED_LANGUAGE
    Given 文書コメントの取り出しに対応していない言語のテストファイル
    When ドリフト検査を実行する
    Then UNSUPPORTED_LANGUAGEエラーが返る
    And 空の判定を返さない
    """
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, "-- テスト\n", name="drift_test.hs")

    result = _engine().run(spec_path=str(spec_path), test_file_path=str(test_path),
                           binding=scenario_binding(test_path.parent.parent.parent))

    assert isinstance(result, Err), result
    assert result.details[0] == "UNSUPPORTED_LANGUAGE"


# ── 全体を検査する ──────────────────────────────────────

def _tree(tmp_path: Path) -> tuple[Path, Path]:
    """相手のいるspecと、いないspecを1つずつ持つ木を作る。"""
    docs = tmp_path / "documents" / "specs" / "bc-x" / "subdomain" / "sd-x" / "usecase"
    docs.mkdir(parents=True)
    _spec(docs, _scenario("対応がある"), document_id="uc-paired", name="uc-paired.json")
    _spec(docs, _scenario("対応がない"), _scenario("これもない"),
          document_id="uc-unpaired", name="uc-unpaired.json")

    tests = tmp_path / "tests" / "application" / "acceptance"
    tests.mkdir(parents=True)
    _test_file(tests, _py(("test_paired", "対応がある")), name="test_uc_paired.py")
    return tmp_path / "documents", tmp_path / "tests"


def test_sweep_lists_scenarios_without_test_file(tmp_path):
    """
    Scenario: 全体を検査すると相手のいないシナリオが並ぶ
    Given シナリオを宣言するが、配置の規約が定めるテストファイルが存在しないspec
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then missing_test_fileにその文書の識別子とブロック種別とシナリオ件数が含まれる
    """
    documents_root, tests_root = _tree(tmp_path)

    result = _engine().run(documents_root=str(documents_root), tests_root=str(tests_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    assert [(m["documentId"], m["block"], m["scenarioCount"])
            for m in result.value["missing_test_file"]] == [
        ("uc-unpaired", "acceptanceScenarios", 2)]


def test_sweep_reports_paired_results(tmp_path):
    """
    Scenario: 全体を検査すると相手が居た組の判定が並ぶ
    Given 配置の規約が定めるテストファイルが存在するspec
    When spec documentの置き場所とテストの配置ルートを指定して検査する
    Then resultsにその文書の識別子と、1組で検査したときと同じ6フィールドが含まれる
    """
    documents_root, tests_root = _tree(tmp_path)

    result = _engine().run(documents_root=str(documents_root), tests_root=str(tests_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    results = result.value["results"]
    assert len(results) == 1
    assert results[0]["documentId"] == "uc-paired"
    assert results[0]["matched"] == [{"scenarioName": "対応がある", "testName": "test_paired"}]
    assert results[0]["missing_in_tests"] == []


def test_both_invocation_styles_rejected(tmp_path):
    """
    Scenario: 1組の指定と全体の指定を同時に渡すと拒む
    Given specとテストファイルの組の指定と、置き場所の指定の両方
    When ドリフト検査を実行する
    Then MISSING_PARAMエラーが返る
    """
    documents_root, tests_root = _tree(tmp_path)
    spec_path = _spec(tmp_path, _scenario("何かが起きる"))
    test_path = _test_file(tmp_path, "def test_x():\n    pass\n")

    result = _engine().run(spec_path=str(spec_path), test_file_path=str(test_path),
                           documents_root=str(documents_root), tests_root=str(tests_root))

    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_PARAM"


def test_no_invocation_style_rejected():
    """
    Scenario: どちらの指定も渡さないと拒む
    Given 組の指定も置き場所の指定も無い
    When ドリフト検査を実行する
    Then MISSING_PARAMエラーが返る
    And 空の判定を返さない
    """
    result = _engine().run()

    assert isinstance(result, Err), result
    assert result.details[0] == "MISSING_PARAM"

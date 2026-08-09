"""片側だけを渡したときに、もう片方を宣言から解決することのテスト。

仕様のシナリオには対応しない、規約由来のテスト。
どのテストがどのspecに対応するかは規約が宣言しており、呼び出し側が
推測する必要はない。推測させると、呼び出し側ごとに配置の写しが増える。
"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)
from waffle.application.usecases.check_scenario_drift import CheckScenarioDrift
from waffle.shared.result import Ok

from tests.fakes import scenario_binding

DOC_BODY = "    Given あ\n    When い\n    Then う"


def _engine() -> CheckScenarioDrift:
    return CheckScenarioDrift(FsDocumentRepository(), TreeSitterTestFunctionExtractor())


def _tree(tmp_path: Path) -> tuple[Path, Path]:
    """spec と、規約が定める位置に置いたテストを1組作る。"""
    docs = tmp_path / "documents" / "specs" / "bc-x" / "subdomain" / "sd-x" / "usecase"
    docs.mkdir(parents=True)
    (docs / ("uc-demo." + "json")).write_text(json.dumps({
        "documentId": "uc-demo", "schemaRef": "DomainSpecSchema/v8", "specKind": "usecase",
        "content": {"acceptanceScenarios": {"scenarios": [
            {"name": "あるシナリオ", "gherkin": f"Scenario: あるシナリオ\n{DOC_BODY}"}]}},
    }, ensure_ascii=False), encoding="utf-8")

    tests = tmp_path / "tests" / "application" / "acceptance"
    tests.mkdir(parents=True)
    (tests / ("test_uc_demo." + "py")).write_text(
        f'def test_demo():\n    """\n    Scenario: あるシナリオ\n{DOC_BODY}\n    """\n',
        encoding="utf-8")
    return tmp_path / "documents", tmp_path / "tests"


def test_resolves_spec_from_test_path(tmp_path):
    """テストのパスだけ渡すと、対応するspecを宣言から引いて突き合わせる。"""
    documents_root, tests_root = _tree(tmp_path)
    test_path = tests_root / "application" / "acceptance" / ("test_uc_demo." + "py")

    result = _engine().run(test_file_path=str(test_path), documents_root=str(documents_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    assert [r["documentId"] for r in result.value["results"]] == ["uc-demo"]
    assert result.value["results"][0]["missing_in_tests"] == []


def test_unresolvable_test_path_is_reported(tmp_path):
    """対応するspecが見つからないテストは、黙って通さず相手なしとして報告する。"""
    documents_root, tests_root = _tree(tmp_path)
    stray = tests_root / "application" / "acceptance" / ("test_uc_nothing." + "py")
    stray.write_text("def test_x():\n    pass\n", encoding="utf-8")

    result = _engine().run(test_file_path=str(stray), documents_root=str(documents_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    assert result.value["results"] == []
    assert [m["expectedPath"] for m in result.value["missing_test_file"]] == [str(stray)]


def test_resolves_tests_from_spec_path(tmp_path):
    """specのパスだけ渡すと、対応するテストを宣言から引いて突き合わせる。"""
    documents_root, tests_root = _tree(tmp_path)
    spec_path = documents_root / "specs" / "bc-x" / "subdomain" / "sd-x" / "usecase" / ("uc-demo." + "json")

    result = _engine().run(spec_path=str(spec_path), documents_root=str(documents_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    assert result.value["missing_test_file"] == []
    assert [r["documentId"] for r in result.value["results"]] == ["uc-demo"]


def test_reports_missing_test_from_spec_path(tmp_path):
    """specのパスだけ渡し、規約が定める位置にテストが無ければ相手なしとして並ぶ。"""
    documents_root, tests_root = _tree(tmp_path)
    (tests_root / "application" / "acceptance" / ("test_uc_demo." + "py")).unlink()
    spec_path = documents_root / "specs" / "bc-x" / "subdomain" / "sd-x" / "usecase" / ("uc-demo." + "json")

    result = _engine().run(spec_path=str(spec_path), documents_root=str(documents_root),
                           binding=scenario_binding(tests_root))

    assert isinstance(result, Ok), result
    assert [m["documentId"] for m in result.value["missing_test_file"]] == ["uc-demo"]

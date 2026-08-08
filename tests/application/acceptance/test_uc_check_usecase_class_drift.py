"""uc-check-usecase-class-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor
from waffle.application.services.source_root_resolution import SearchUnit
from waffle.application.usecases.check_usecase_class_drift import CheckUsecaseClassDrift
from waffle.shared.result import Ok

from tests.fakes import JAVA_NAMING, PYTHON_NAMING


def _engine() -> CheckUsecaseClassDrift:
    return CheckUsecaseClassDrift(FsDocumentRepository(), TreeSitterClassExtractor())


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _usecase_doc(operation_name: str) -> dict:
    return {
        "documentId": "uc-a",
        "specKind": "usecase",
        "content": {"usecase": {"blockType": "Usecase", "title": "名前", "operationName": operation_name}},
    }


def test_all_usecase_operations_match_implementation(tmp_path):
    """
    Scenario: 全usecaseの操作名と実装クラスが一致するとき差分なしと判定する
    Given 全usecaseのoperationNameが、対応する実装ファイル内の同名クラスと一致するspecツリー
    When クラス名ドリフト検査を実行する
    Then missing_implementation_file・class_name_mismatch両方が空配列で返る
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    (src_root).mkdir(parents=True, exist_ok=True)
    (src_root / "check_scenario_drift.py").write_text(
        "class CheckScenarioDrift:\n    pass\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value == {"missing_implementation_file": [], "missing_implementation_in_scope": [], "class_name_mismatch": []}


def test_usecase_without_implementation_file(tmp_path):
    """
    Scenario: 実装ファイルが存在しないusecaseを検出する
    Given operationNameから導出したファイルパスに対応する実装ファイルが実在しないusecase document
    When クラス名ドリフト検査を実行する
    Then missing_implementation_fileにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "uc-a", "operationName": "CheckScenarioDrift", "expectedPath": str(src_root / "check_scenario_drift.py")}
    ]


def test_detects_class_drift_in_java_implementation(tmp_path):
    """
    Scenario: Java実装に対してもクラス名ドリフトを検知できる
    Given languageにjavaを指定し、operationNameと一致するJavaクラスを持つ実装ファイル
    When クラス名ドリフト検査を実行する
    Then 対象言語に依らず正しく一致と判定される
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)
    # Javaは公開クラスを含むファイルの名前が型名と一致していないとコンパイルできない
    (src_root / "CheckScenarioDrift.java").write_text(
        "public class CheckScenarioDrift {\n    private String x;\n}\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root), JAVA_NAMING, language="java")
    assert isinstance(result, Ok), result
    assert result.value == {"missing_implementation_file": [], "missing_implementation_in_scope": [], "class_name_mismatch": []}


def test_usecase_with_mismatched_class_name(tmp_path):
    """
    Scenario: クラス名が一致しないusecaseを検出する
    Given 実装ファイルは実在するが、operationNameと一致するクラス定義を持たないusecase document
    When クラス名ドリフト検査を実行する
    Then class_name_mismatchにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "check_scenario_drift.py").write_text(
        "class SomethingElse:\n    pass\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value["class_name_mismatch"] == [
        {
            "documentId": "uc-a",
            "operationName": "CheckScenarioDrift",
            "expectedPath": str(src_root / "check_scenario_drift.py"),
            "foundClasses": ["SomethingElse"],
        }
    ]


def test_directory_scope_reports_missing_in_scope(tmp_path):
    """
    Scenario: 宣言がなければ配置ディレクトリのどこにも無いことを報告する
    Given granularityがusecaseにperFileを宣言していないarchitecture
    And 操作名と一致するクラスが配置ディレクトリのどこにも無い
    When 操作と実装の食い違いを調べる
    Then その組がmissing_implementation_in_scopeに現れる
    And 探した配置ディレクトリがsearchedRootとして添えられている
    And missing_implementation_fileは空のままである
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "other.py").write_text("class SomethingElse:\n    pass\n", encoding="utf-8")

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING,
                           root_search_unit=SearchUnit(per_file=False, root=str(src_root)))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_in_scope"] == [
        {"documentId": "uc-a", "operationName": "CheckScenarioDrift",
         "concept": "usecase", "searchedRoot": str(src_root)}
    ]
    assert result.value["missing_implementation_file"] == []


def test_file_scope_reports_only_missing_file(tmp_path):
    """
    Scenario: 宣言があればファイルの不在だけを報告する
    Given granularityがusecaseにperFile 1を宣言しているarchitecture
    And 操作名から導出したファイルが存在しない
    When 操作と実装の食い違いを調べる
    Then その組がmissing_implementation_fileに現れる
    And missing_implementation_in_scopeは空のままである
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING,
                           root_search_unit=SearchUnit(per_file=True))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "uc-a", "operationName": "CheckScenarioDrift",
         "expectedPath": str(src_root / "check_scenario_drift.py")}
    ]
    assert result.value["missing_implementation_in_scope"] == []

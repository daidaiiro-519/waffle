"""uc-check-usecase-class-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor
from waffle.application.usecases.check_usecase_class_drift import CheckUsecaseClassDrift
from waffle.shared.result import Ok


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


def test_全usecaseの操作名と実装クラスが一致するとき差分なしと判定する(tmp_path):
    """
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

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value == {"missing_implementation_file": [], "class_name_mismatch": []}


def test_実装ファイルが存在しないusecaseを検出する(tmp_path):
    """
    Given operationNameから導出したファイルパスに対応する実装ファイルが実在しないusecase document
    When クラス名ドリフト検査を実行する
    Then missing_implementation_fileにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["missing_implementation_file"] == [
        {"documentId": "uc-a", "operationName": "CheckScenarioDrift", "expectedPath": str(src_root / "check_scenario_drift.py")}
    ]


def test_Java実装に対してもクラス名ドリフトを検知できる(tmp_path):
    """
    Given languageにjavaを指定し、operationNameと一致するJavaクラスを持つ実装ファイル
    When クラス名ドリフト検査を実行する
    Then Python専用のASTに依存せず、tree-sitter経由で正しく一致と判定される
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("CheckScenarioDrift"))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "check_scenario_drift.java").write_text(
        "public class CheckScenarioDrift {\n    private String x;\n}\n", encoding="utf-8"
    )

    result = _engine().run(str(docs_root), str(src_root), language="java")
    assert isinstance(result, Ok), result
    assert result.value == {"missing_implementation_file": [], "class_name_mismatch": []}


def test_クラス名が一致しないusecaseを検出する(tmp_path):
    """
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

    result = _engine().run(str(docs_root), str(src_root))
    assert isinstance(result, Ok), result
    assert result.value["class_name_mismatch"] == [
        {
            "documentId": "uc-a",
            "operationName": "CheckScenarioDrift",
            "expectedPath": str(src_root / "check_scenario_drift.py"),
            "foundClasses": ["SomethingElse"],
        }
    ]

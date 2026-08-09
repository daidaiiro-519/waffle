"""uc-check-operation-drift の受け入れテスト（ネイティブpytest）。"""
import json
from pathlib import Path

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_operation_drift import CheckOperationDrift
from waffle.shared.result import Ok

from tests.fakes import JAVA_NAMING, PYTHON_NAMING


def _engine() -> CheckOperationDrift:
    return CheckOperationDrift(FsDocumentRepository())


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _usecase_doc(operation_name: str, operations: list[str]) -> dict:
    return {
        "documentId": "uc-a",
        "specKind": "usecase",
        "content": {
            "usecase": {"blockType": "Usecase", "title": "名前", "operationName": operation_name},
            "acceptanceScenarios": {
                "blockType": "AcceptanceScenarios",
                "title": "受け入れシナリオ",
                "background": "",
                "scenarios": [{"name": f"s{i}", "operation": op} for i, op in enumerate(operations)],
            },
        },
    }


def test_declared_and_implemented_operations_match(tmp_path):
    """
    Scenario: 宣言と実装のoperationが完全一致するとき差分なしと判定する
    Given specが宣言するoperation名の集合と、実装のoperation分岐の集合が完全一致するusecase
    When operationドリフト検査を実行する
    Then operations_missing_in_impl・operations_undocumented_in_spec両方が空配列で返る
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("QueryDocument", ["get_block", "filter_items"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "query_document.py").write_text(
        'if operation == "get_block":\n    pass\nelif operation == "filter_items":\n    pass\n',
        encoding="utf-8",
    )

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value == {"operations_missing_in_impl": [], "operations_undocumented_in_spec": []}


def test_operation_declared_but_not_implemented(tmp_path):
    """
    Scenario: specが宣言するが実装に無いoperationを検出する
    Given specが宣言するが実装のoperation分岐には存在しないoperation名
    When operationドリフト検査を実行する
    Then operations_missing_in_implにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("QueryDocument", ["get_block", "renamed_op"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "query_document.py").write_text('if operation == "get_block":\n    pass\n', encoding="utf-8")

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value["operations_missing_in_impl"] == [
        {"documentId": "uc-a", "operation": "renamed_op", "expectedPath": str(src_root / "query_document.py")}
    ]


def test_operation_implemented_but_not_declared(tmp_path):
    """
    Scenario: 実装にあるがspecに未宣言のoperationを検出する
    Given 実装のoperation分岐にはあるがspecのどのシナリオにも宣言されていないoperation
    When operationドリフト検査を実行する
    Then operations_undocumented_in_specにその組が含まれる
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("QueryDocument", ["get_block"]))
    src_root.mkdir(parents=True, exist_ok=True)
    (src_root / "query_document.py").write_text(
        'if operation == "get_block":\n    pass\nelif operation == "undocumented_op":\n    pass\n',
        encoding="utf-8",
    )

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value["operations_undocumented_in_spec"] == [
        {"documentId": "uc-a", "operation": "undocumented_op", "expectedPath": str(src_root / "query_document.py")}
    ]


def test_usecase_without_declared_operations_is_skipped(tmp_path):
    """
    Scenario: operationを1件も宣言していないusecaseは対象外
    Given acceptanceScenariosのどのシナリオにもoperationフィールドを宣言していないusecase
    When operationドリフト検査を実行する
    Then そのusecaseは突き合わせの対象にならず、差分にも現れない
    """
    docs_root = tmp_path / "documents"
    src_root = tmp_path / "src"
    _write(docs_root / "usecase" / "uc-a.json", _usecase_doc("ValidateDocument", []))
    src_root.mkdir(parents=True, exist_ok=True)

    result = _engine().run(str(docs_root), str(src_root), PYTHON_NAMING)
    assert isinstance(result, Ok), result
    assert result.value == {"operations_missing_in_impl": [], "operations_undocumented_in_spec": []}

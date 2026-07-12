"""check operation drift — usecase specのacceptanceScenariosが宣言するoperation名と、
対応する実装ファイルが実際に持つoperation分岐の文字列が一致しているかを検証する
application use case。

acceptanceScenariosにoperationフィールドを1件も宣言していないusecase（単一操作の
usecase等）は対象外（宣言が無ければ突き合わせようがないため）。実行/意味理解はしない
（宣言されたoperation名の集合と、実装ソース中のoperation比較文字列の集合の機械的な
突き合わせのみ）。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.canonical_naming import operation_name_to_module_name
from waffle.domain.services.operation_drift import declared_operations, implemented_operations
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckOperationDrift:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, documents_root: str, src_root: str) -> Result[dict]:
        if not is_confined(documents_root) or not is_confined(src_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            doc_paths = self._documents.list_files(documents_root, "**/*.json")
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")
        try:
            self._documents.list_dirs(src_root)
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {src_root}")

        operations_missing_in_impl: list[dict] = []
        operations_undocumented_in_spec: list[dict] = []

        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "usecase":
                continue
            declared = declared_operations(doc)
            if not declared:
                continue
            operation_name = doc.get("content", {}).get("name", {}).get("operationName")
            module_name = operation_name_to_module_name(operation_name) if operation_name else None
            expected_path = f"{src_root}/{module_name}.py" if module_name else None
            try:
                source = self._documents.read_text(expected_path) if expected_path else ""
            except FileNotFoundError:
                source = ""
            implemented = implemented_operations(source)

            for op in sorted(declared - implemented):
                operations_missing_in_impl.append({
                    "documentId": doc["documentId"], "operation": op, "expectedPath": expected_path,
                })
            for op in sorted(implemented - declared):
                operations_undocumented_in_spec.append({
                    "documentId": doc["documentId"], "operation": op, "expectedPath": expected_path,
                })

        return Ok({
            "operations_missing_in_impl": operations_missing_in_impl,
            "operations_undocumented_in_spec": operations_undocumented_in_spec,
        })

"""check usecase class drift — usecase specが宣言する操作名(content.name.operationName)
と、対応する実装クラスが実際に持つクラス名が一致しているかを検証する application use case。

「モデルはコードに宿る」というDDD原則に基づき、宣言と実装クラスの対応関係という、
他のどのreconcile usecaseも見ていない盲点を機械的に検出する。実行/意味理解はしない
（宣言された名前と、実装ファイル内のクラス定義名の機械的な突き合わせのみ）。

クラス名抽出はClassDeclarationExtractor port経由で行い、Python専用のASTには
依存しない（tree-sitterベースのadapterでPython/Java/TypeScript/JavaScriptに
対応、docs/brainstorm/brainstorm-waffle-hooks.md参照）。
"""
from __future__ import annotations

from waffle.application.ports.class_declaration_extractor import ClassDeclarationExtractor
from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.canonical_naming import language_extension, operation_name_to_module_name
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckUsecaseClassDrift:
    def __init__(self, documents: DocumentRepository, extractor: ClassDeclarationExtractor) -> None:
        self._documents = documents
        self._extractor = extractor

    def run(self, documents_root: str, src_root: str, language: str = "python") -> Result[dict]:
        if not is_confined(documents_root) or not is_confined(src_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            extension = language_extension(language)
        except ValueError as e:
            return _err("UNSUPPORTED_LANGUAGE", str(e))
        try:
            doc_paths = self._documents.list_files(documents_root, "**/*.json")
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")
        try:
            self._documents.list_dirs(src_root)
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {src_root}")

        missing_implementation_file: list[dict] = []
        class_name_mismatch: list[dict] = []

        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "usecase":
                continue
            operation_name = doc.get("content", {}).get("name", {}).get("operationName")
            if not operation_name:
                continue
            module_name = operation_name_to_module_name(operation_name)
            expected_path = f"{src_root}/{module_name}.{extension}"
            try:
                source = self._documents.read_text(expected_path)
            except FileNotFoundError:
                missing_implementation_file.append({
                    "documentId": doc["documentId"], "operationName": operation_name, "expectedPath": expected_path,
                })
                continue
            found_classes = self._extractor.class_names(source, language)
            if operation_name not in found_classes:
                class_name_mismatch.append({
                    "documentId": doc["documentId"], "operationName": operation_name,
                    "expectedPath": expected_path, "foundClasses": found_classes,
                })

        return Ok({
            "missing_implementation_file": missing_implementation_file,
            "class_name_mismatch": class_name_mismatch,
        })

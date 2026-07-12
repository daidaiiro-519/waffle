"""check aggregate class drift — aggregate specが宣言する集約ルート名
(content.aggregateRoot.name)と、対応する実装クラスが実際に持つクラス名が
一致しているかを検証する application use case。

check_usecase_class_drift.pyと同型の検知を集約にも適用する。「モデルはコードに
宿る」というDDD原則に基づき、宣言と実装クラスの対応関係を機械的に検出する。
実行/意味理解はしない（宣言された名前と、実装ファイル内のクラス定義名の機械的な
突き合わせのみ）。

クラス名・フィールド名抽出はClassDeclarationExtractor port経由で行い、Python
専用のASTには依存しない（tree-sitterベースのadapterでPython/Java/TypeScript/
JavaScriptに対応、docs/brainstorm/brainstorm-waffle-hooks.md参照）。
"""
from __future__ import annotations

from waffle.application.ports.class_declaration_extractor import ClassDeclarationExtractor
from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.canonical_naming import language_extension, operation_name_to_module_name, to_snake_case
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _declared_attributes(doc: dict, root_name: str) -> list[str]:
    entities = doc.get("content", {}).get("entities", {}).get("items", [])
    root = next((e for e in entities if e.get("name") == root_name), None)
    if root is None:
        return []
    return [to_snake_case(a["name"]) for a in root.get("attributes", [])]


def _declared_value_objects(doc: dict) -> list[str]:
    return [v["name"] for v in doc.get("content", {}).get("valueObjects", {}).get("items", [])]


def _declared_value_object_attributes(doc: dict, vo_name: str) -> list[str] | None:
    """値オブジェクトitemがattributesを宣言していればsnake_case変換したリストを返す。
    未宣言（旧形式のdocument）ならNone（属性レベルの突き合わせをスキップする合図）。"""
    items = doc.get("content", {}).get("valueObjects", {}).get("items", [])
    vo = next((v for v in items if v.get("name") == vo_name), None)
    if vo is None or "attributes" not in vo:
        return None
    return [to_snake_case(a["name"]) for a in vo["attributes"]]


class CheckAggregateClassDrift:
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
        attribute_mismatch: list[dict] = []
        missing_value_object: list[dict] = []
        value_object_attribute_mismatch: list[dict] = []

        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "aggregate":
                continue
            root_name = doc.get("content", {}).get("aggregateRoot", {}).get("name")
            if not root_name:
                continue
            module_name = operation_name_to_module_name(root_name)
            expected_path = f"{src_root}/{module_name}.{extension}"
            try:
                source = self._documents.read_text(expected_path)
            except FileNotFoundError:
                missing_implementation_file.append({
                    "documentId": doc["documentId"], "aggregateRootName": root_name, "expectedPath": expected_path,
                })
                continue
            found_classes = self._extractor.class_names(source, language)
            for vo_name in _declared_value_objects(doc):
                if vo_name not in found_classes:
                    missing_value_object.append({
                        "documentId": doc["documentId"], "aggregateRootName": root_name,
                        "valueObjectName": vo_name, "expectedPath": expected_path,
                    })
                    continue
                declared_vo_attributes = _declared_value_object_attributes(doc, vo_name)
                if declared_vo_attributes:
                    found_vo_fields = self._extractor.field_names(source, language, vo_name)
                    if set(declared_vo_attributes) != set(found_vo_fields):
                        value_object_attribute_mismatch.append({
                            "documentId": doc["documentId"], "aggregateRootName": root_name,
                            "valueObjectName": vo_name, "expectedPath": expected_path,
                            "declaredAttributes": declared_vo_attributes, "foundFields": found_vo_fields,
                        })
            if root_name not in found_classes:
                class_name_mismatch.append({
                    "documentId": doc["documentId"], "aggregateRootName": root_name,
                    "expectedPath": expected_path, "foundClasses": found_classes,
                })
                continue
            declared_attributes = _declared_attributes(doc, root_name)
            found_fields = self._extractor.field_names(source, language, root_name)
            if declared_attributes and set(declared_attributes) != set(found_fields):
                attribute_mismatch.append({
                    "documentId": doc["documentId"], "aggregateRootName": root_name,
                    "expectedPath": expected_path,
                    "declaredAttributes": declared_attributes, "foundFields": found_fields,
                })

        return Ok({
            "missing_implementation_file": missing_implementation_file,
            "class_name_mismatch": class_name_mismatch,
            "attribute_mismatch": attribute_mismatch,
            "missing_value_object": missing_value_object,
            "value_object_attribute_mismatch": value_object_attribute_mismatch,
        })

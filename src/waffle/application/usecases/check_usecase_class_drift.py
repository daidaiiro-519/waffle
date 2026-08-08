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
from waffle.application.services.class_index import build_class_index
from waffle.application.services.source_root_resolution import SearchUnit
from waffle.domain.services.canonical_naming import file_name
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckUsecaseClassDrift:
    def __init__(self, documents: DocumentRepository, extractor: ClassDeclarationExtractor) -> None:
        self._documents = documents
        self._extractor = extractor

    def run(self, documents_root: str, src_root: str, naming: dict,
            language: str = "python",
            root_search_unit: SearchUnit | None = None) -> Result[dict]:
        if not is_confined(documents_root) or not is_confined(src_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            doc_paths = self._documents.list_files(documents_root, "**/*.json")
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")
        # 宣言された配置がまだ存在しないことは、引数の誤りではなくドリフトそのもの。
        # 規約を先に書いて実装を後から合わせる進め方では、この状態が正常に起こる。
        # ここで止めると「まだ何も出来ていない」ことを報告できない

        missing_implementation_file: list[dict] = []
        missing_implementation_in_scope: list[dict] = []
        class_name_mismatch: list[dict] = []

        # 探し方は architecture の宣言が決める。渡されなければファイル単位
        unit = root_search_unit or SearchUnit(per_file=True)
        scope_index = (
            build_class_index(self._documents, self._extractor,
                              unit.root or src_root, naming["fileNameSuffix"], language)
            if not unit.per_file else None)

        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "usecase":
                continue
            if doc.get("status") == "SUPERSEDED":
                # 廃止済みspecは実装が意図的に存在しない（例: document-graph Skillへの
                # 移管でWaffle内部実装を削除したケース）。ドリフトとして検出しない。
                continue
            operation_name = doc.get("content", {}).get("usecase", {}).get("operationName")
            if not operation_name:
                continue
            if scope_index is not None:
                # 配置ディレクトリのどこかにあればよい。無いことは「あるはずの
                # 1ファイルが無い」とは別の事実なので、別の器へ入れる
                if operation_name not in scope_index:
                    missing_implementation_in_scope.append({
                        "documentId": doc["documentId"], "operationName": operation_name,
                        "concept": "usecase", "searchedRoot": unit.root or src_root,
                    })
                continue
            expected_path = f"{src_root}/{file_name(operation_name, naming)}"
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
            "missing_implementation_in_scope": missing_implementation_in_scope,
            "class_name_mismatch": class_name_mismatch,
        })

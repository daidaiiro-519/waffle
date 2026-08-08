"""check surface drift — ユースケースが宣言する入力と、その操作を外へ差し出している
口が実際に受け取る入力を突き合わせる application use case。

口の種類は問わない。命令行でも道具呼び出しでも要求本文でも、同じ宣言を指している
かだけを見る。取り出し方の違いは SurfaceExtractor port が吸収する。

どの入口がどの操作の口かは、入口が参照している名前と宣言された操作名の一致で決める。
関数の名前では決めない——口ごとに命名の流儀が違い、実際 CLI と MCP で同じ操作の
入口が別の名前を持っている。

綴りは区切りと大文字小文字を落として比べる。同じ入力が口ごとに違う綴りで現れるのは
正常で、どの綴りが正しいかはこの操作の関心ではない。
"""
from __future__ import annotations

import re

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.surface_extractor import SurfaceExtractor
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result

_NOT_ALPHANUMERIC = re.compile(r"[^0-9a-z]")


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _normalized(name: str) -> str:
    """綴りの流儀を落として、名前を突き合わせられる形にする。

    Args:
        name: 突き合わせたい名前。

    Returns:
        区切りと大文字小文字を落とした形。

    Raises:
        なし。
    """
    return _NOT_ALPHANUMERIC.sub("", name.lower())


def _declared_inputs(doc: dict) -> list[str] | None:
    """そのユースケースが宣言している入力の名前を取り出す。

    Args:
        doc: ユースケースのspec document。

    Returns:
        宣言された入力の名前。1つも宣言していなければ None。

    Raises:
        なし。
    """
    items = doc.get("content", {}).get("inputs", {}).get("items") or []
    names = [item["name"] for item in items if item.get("name")]
    return names or None


class CheckSurfaceDrift:
    """宣言された入力と、口が実際に受け取る入力の食い違いを見つける。"""

    def __init__(self, documents: DocumentRepository, extractor: SurfaceExtractor) -> None:
        self._documents = documents
        self._extractor = extractor

    def run(self, documents_root: str, surface_paths: list[str],
            language: str = "python") -> Result[dict]:
        """宣言された入力と、口が受け取る入力を突き合わせる。

        Args:
            documents_root: 突き合わせの対象とするユースケース仕様の置き場所。
            surface_paths: 外へ差し出している口のソースの一覧。
            language: 口のソースの言語。

        Returns:
            missing_input と undeclared_input を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        if not is_confined(documents_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            doc_paths = self._documents.list_files(documents_root, "**/*.json")
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")

        # 操作名 -> (documentId, 宣言された入力)。入力を宣言していないものは持たない
        declared: dict[str, tuple[str, list[str]]] = {}
        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "usecase":
                continue
            operation_name = doc.get("content", {}).get("usecase", {}).get("operationName")
            inputs = _declared_inputs(doc)
            if operation_name and inputs:
                declared[operation_name] = (doc["documentId"], inputs)

        missing_input: list[dict] = []
        undeclared_input: list[dict] = []

        for surface_path in surface_paths:
            if not is_confined(surface_path):
                return _err("INVALID_PATH", "パストラバーサルは許可されません")
            try:
                source = self._documents.read_text(surface_path)
            except FileNotFoundError:
                continue
            for entry in self._extractor.surfaces(source, language):
                for reference in entry["references"]:
                    if reference not in declared:
                        continue
                    document_id, inputs = declared[reference]
                    taken = {_normalized(p): p for p in entry["params"]}
                    wanted = {_normalized(n): n for n in inputs}
                    for key, name in wanted.items():
                        if key not in taken:
                            missing_input.append({
                                "documentId": document_id, "operationName": reference,
                                "inputName": name, "surfacePath": surface_path,
                            })
                    for key, name in taken.items():
                        if key not in wanted:
                            undeclared_input.append({
                                "documentId": document_id, "operationName": reference,
                                "inputName": name, "surfacePath": surface_path,
                            })

        return Ok({
            "missing_input": missing_input,
            "undeclared_input": undeclared_input,
        })

"""stack_resolution — architectureRef から、同じスタックの他の規約文書を引く。

CodingSchema は1スタック＝複数の codingKind document を stack フィールドで
束ねる。検査がファイル名を組み立てるための表記規則は coding-standard が持ち、
配置は architecture が持つため、片方の参照からもう片方を辿る必要がある。

この引き当てをコード側の固定表にすると、スタックが増えるたびに写しが増える。
stack フィールドという既にある宣言を辿ることで、対応を持たずに済ませる。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.shared.result import Err, Ok, Result

__all__ = ["resolve_naming"]

CODING_ROOT = ".waffle/documents/coding"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _load_coding_documents(documents: DocumentRepository) -> list[dict]:
    try:
        paths = documents.list_files(CODING_ROOT, "**/*." + "json")
    except FileNotFoundError:
        return []
    loaded = []
    for path in paths:
        try:
            loaded.append(documents.load(path))
        except FileNotFoundError:
            continue
    return loaded


def resolve_naming(documents: DocumentRepository, architecture_ref: str) -> Result[dict]:
    """architectureRef が属するスタックの coding-standard から naming ブロックを返す。

    Args:
        documents: 規約文書を読むための DocumentRepository。
        architecture_ref: architecture document の documentId。

    Returns:
        naming ブロックを持つ Ok、または失敗を表す Err。
        失敗のコードは ARCHITECTURE_REF_NOT_FOUND / CODING_STANDARD_NOT_FOUND。
    """
    coding_documents = _load_coding_documents(documents)
    architecture = next(
        (d for d in coding_documents if d.get("documentId") == architecture_ref), None)
    if architecture is None:
        return _err("ARCHITECTURE_REF_NOT_FOUND",
                    f"architecture document が見つかりません: {architecture_ref}")
    stack = architecture.get("stack")
    standard = next(
        (d for d in coding_documents
         if d.get("codingKind") == "coding-standard" and d.get("stack") == stack), None)
    if standard is None:
        return _err("CODING_STANDARD_NOT_FOUND",
                    f"stack={stack} の coding-standard が見つかりません"
                    f"（{architecture_ref} と同じスタックの命名規約が必要）")
    return Ok(standard.get("content", {}).get("naming", {}))

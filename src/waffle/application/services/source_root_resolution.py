"""source_root_resolution — architecture文書から概念の実装配置を解決する application層の共通ヘルパー。

CLIとMCPの両方がこの解決を必要とし、以前は同じ判定が両方の合成ルートに重複して
置かれていた。合成ルートは配線専用に保つ規約（コンポジションルート自体に業務
ロジックを書かない）に反しており、かつ inbound adapter が domain service を
直接呼ぶ形になっていた。判断をここへ引き上げ、アダプターはResultを各プロトコルの
形へ translate するだけにする。

配置の導出そのもの（sourceRootとplacementの結合）は業務判断を含まない計算なので
domain/services/concept_source_root.py が担う。ここはport経由の読込と、
どのエラーコードで失敗を表すかの編成だけを担当する。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.concept_source_root import (
    package_name_from_reference,
    resolve_source_root,
)
from waffle.shared.result import Err, Ok, Result

__all__ = ["resolve_src_root"]

_ARCHITECTURE_PATH = ".waffle/documents/coding/{architecture_ref}.json"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def resolve_src_root(
    documents: DocumentRepository,
    src_root: str | None,
    architecture_ref: str | None,
    concept: str,
) -> Result[str]:
    """実装ファイルの配置ルートを解決する。

    src_root が明示されていればそれを優先し、無ければ architecture_ref が指す
    architecture文書の layout.sourceRoot と conceptPlacement から導出する。

    Args:
        documents: architecture文書を読むためのDocumentRepository。
        src_root: 明示指定された配置ルート。指定されていれば他を見ない。
        architecture_ref: 参照するarchitecture documentのdocumentId。
        concept: 解決したい概念（usecase / aggregate 等）。

    Returns:
        解決した配置ルートを持つ Ok、または失敗を表す Err。
        失敗のコードは MISSING_PARAM / ARCHITECTURE_REF_NOT_FOUND /
        ARCHITECTURE_REF_UNRESOLVED のいずれか。
    """
    if src_root:
        return Ok(src_root)
    if not architecture_ref:
        return _err("MISSING_PARAM", "srcRoot または architectureRef のいずれかが必要です")
    try:
        document = documents.load(_ARCHITECTURE_PATH.format(architecture_ref=architecture_ref))
    except FileNotFoundError:
        return _err(
            "ARCHITECTURE_REF_NOT_FOUND",
            f"architecture document が見つかりません: {architecture_ref}",
        )
    content = document.get("content", {})
    resolved = resolve_source_root(
        content.get("layout", {}),
        content.get("conceptPlacement", {}).get("items", []),
        concept,
        package=package_name_from_reference(architecture_ref, "architecture") or "",
    )
    if not resolved:
        return _err(
            "ARCHITECTURE_REF_UNRESOLVED",
            f"{architecture_ref} の layout.sourceRoot / conceptPlacement"
            f"（concept={concept}）から解決できません",
        )
    return Ok(resolved)

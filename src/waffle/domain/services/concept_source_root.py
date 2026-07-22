"""concept_source_root — CodingSchemaのarchitecture文書が持つlayout.sourceRootと
conceptPlacementから、指定した概念（usecase等）の実装ファイル配置パスを導出する
純ロジック。drift-check系の複数usecaseが共通して依存する（特定の集約に属さない・
言語/アーキテクチャに依存しない汎用計算）。
"""
from __future__ import annotations

from waffle.domain.services import path_template


def resolve_source_root(layout: dict, concept_placement_items: list[dict], concept: str, **variables) -> str | None:
    """layoutのsourceRootと、concept_placement_itemsの中からconceptに一致する
    placementを結合し、path_template.resolveでvariablesを当てはめて解決する。
    sourceRootが無い、またはconceptが見つからない場合はNoneを返す。"""
    source_root = layout.get("sourceRoot")
    if not source_root:
        return None
    placement = next((item["placement"] for item in concept_placement_items if item.get("concept") == concept), None)
    if placement is None:
        return None
    return path_template.resolve(f"{source_root}/{placement}", **variables)


def package_name_from_reference(reference: str, coding_kind: str) -> str | None:
    """architectureRef等のdocumentId（例: 'architecture-waffle'）から、
    '{codingKind}-' 接頭辞（例: 'architecture-'）を剥がしてproduct名を復元する。
    接頭辞が一致しなければNoneを返す。"""
    prefix = f"{coding_kind}-"
    if not reference.startswith(prefix):
        return None
    return reference[len(prefix):]

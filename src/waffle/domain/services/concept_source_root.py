"""concept_source_root — CodingSchemaのarchitecture文書が持つlayout.sourceRootと
conceptPlacementから、指定した概念（usecase等）の実装ファイル配置パスを導出する
純ロジック。drift-check系の複数usecaseが共通して依存する（特定の集約に属さない・
言語/アーキテクチャに依存しない汎用計算）。
"""
from __future__ import annotations

from waffle.domain.services import path_template


_IMPLEMENTATION_ROLES = ("single", "implementation", "definition")


def _implementation_path(item: dict) -> str | None:
    """1つの概念の配置の中から、実装が置かれる方を選ぶ。

    概念は複数の場所に分かれることがある（インターフェースと実装、宣言と定義）。
    実装ファイルを探すのが目的なので、実装側の役割を優先し、該当が無ければ
    先頭を使う。

    Args:
        item: conceptPlacement の1要素。

    Returns:
        配置パス。placements が空なら None。
    """
    placements = item.get("placements") or []
    for role in _IMPLEMENTATION_ROLES:
        for placement in placements:
            if placement.get("role") == role:
                return placement.get("path")
    return placements[0].get("path") if placements else None


def resolve_source_root(layout: dict, concept_placement_items: list[dict], concept: str, **variables) -> str | None:
    """layoutのsourceRootと、conceptに一致する概念の配置を結合して解決する。

    Args:
        layout: architecture文書の layout ブロック。
        concept_placement_items: conceptPlacement の items。
        concept: 解決したい概念（usecase / aggregate 等）。
        **variables: パステンプレートへ当てはめる変数（package 等）。

    Returns:
        解決した配置パス。sourceRootが無い、conceptが見つからない、
        配置が空のいずれかの場合は None。
    """
    source_root = layout.get("sourceRoot")
    if not source_root:
        return None
    item = next((x for x in concept_placement_items if x.get("concept") == concept), None)
    if item is None:
        return None
    placement = _implementation_path(item)
    if placement is None:
        return None
    return path_template.resolve(f"{source_root}/{placement}", **variables)


def package_name_from_reference(reference: str, coding_kind: str) -> str | None:
    """architectureRef等のdocumentId（例: 'architecture-waffle'）から、
    '{codingKind}-' 接頭辞（例: 'architecture-'）を剥がしてproduct名を復元する。

    Args:
        reference: 参照のdocumentId（例: 'architecture-waffle'）。
        coding_kind: 剥がす接頭辞にあたる種別（例: 'architecture'）。

    Returns:
        復元したproduct名。接頭辞が一致しなければ None。

    Raises:
        なし。
    """
    prefix = f"{coding_kind}-"
    if not reference.startswith(prefix):
        return None
    return reference[len(prefix):]


def declares_per_file(layout: dict, concept: str) -> bool:
    """その概念に「1ファイルに1つ」の粒度が宣言されているか。

    宣言があればファイル単位で探し、無ければ配置ディレクトリ単位で探す。
    どちらかを検査が独自に決めると、宣言と検査が別々に漂流する。

    Args:
        layout: architectureのlayoutブロック。
        concept: 粒度を知りたい概念。

    Returns:
        「1ファイルに1つ」が宣言されていれば True。

    Raises:
        なし。
    """
    for item in layout.get("granularity") or []:
        if item.get("concept") == concept:
            return bool(item.get("perFile"))
    return False

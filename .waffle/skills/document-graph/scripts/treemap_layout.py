"""treemap_layout — squarified treemap（Bruls et al. 1999）による面積比例の矩形分割を
計算する純粋関数群。document-graph Skillのtreemap描画（graph_viewer_html_template）が
使う。Waffle本体の src/waffle/domain/services/treemap_layout.py から無変更で移植した
（このSkill自身はdocument.jsonを一切知らないので、この純粋関数のロジックだけを引き継ぐ）。
"""
from __future__ import annotations


def _layout_row(
    sizes: list[float], x: float, y: float, dx: float, dy: float
) -> list[tuple[float, float, float, float]]:
    covered = sum(sizes)
    if dx >= dy:
        width = covered / dy if dy else 0.0
        rects = []
        cy = y
        for size in sizes:
            h = size / width if width else 0.0
            rects.append((x, cy, width, h))
            cy += h
        return rects
    height = covered / dx if dx else 0.0
    rects = []
    cx = x
    for size in sizes:
        w = size / height if height else 0.0
        rects.append((cx, y, w, height))
        cx += w
    return rects


def _leftover(sizes: list[float], x: float, y: float, dx: float, dy: float) -> tuple[float, float, float, float]:
    covered = sum(sizes)
    if dx >= dy:
        width = covered / dy if dy else 0.0
        return x + width, y, dx - width, dy
    height = covered / dx if dx else 0.0
    return x, y + height, dx, dy - height


def _worst_ratio(sizes: list[float], x: float, y: float, dx: float, dy: float) -> float:
    rects = _layout_row(sizes, x, y, dx, dy)
    return max(max(w / h, h / w) for _, _, w, h in rects if w > 0 and h > 0)


def squarify(sizes: list[float], x: float, y: float, dx: float, dy: float) -> list[tuple[float, float, float, float]]:
    """sizesの合計がdx*dyに正規化されている前提（normalize_sizesを事前に通す）。
    降順ソート済みを推奨（squarified treemapが前提とする並び）。sizesの並び順のまま矩形を返す。
    """
    sizes = [s for s in sizes if s > 0]
    if not sizes or dx <= 0 or dy <= 0:
        return []
    if len(sizes) == 1:
        return _layout_row(sizes, x, y, dx, dy)
    i = 1
    while i < len(sizes) and _worst_ratio(sizes[:i], x, y, dx, dy) >= _worst_ratio(sizes[: i + 1], x, y, dx, dy):
        i += 1
    current = sizes[:i]
    remaining = sizes[i:]
    nx, ny, ndx, ndy = _leftover(current, x, y, dx, dy)
    return _layout_row(current, x, y, dx, dy) + squarify(remaining, nx, ny, ndx, ndy)


def normalize_sizes(sizes: list[float], dx: float, dy: float) -> list[float]:
    """sizesの合計をキャンバス面積（dx*dy）に比例配分する。"""
    total = sum(sizes)
    if total <= 0:
        return [0.0 for _ in sizes]
    area = dx * dy
    return [s * area / total for s in sizes]

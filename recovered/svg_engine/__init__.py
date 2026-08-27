"""svg_engine ── Waffle本体に依存しない、独立したSVGコンポーネントエンジン（PoC）。

構造（節点・辺・囲み）とスタイル（色・寸法・角丸等）を分けて持つ。新しい
描画部品は registry.py の台帳へ登録するだけで足せる。tokens.py のテーマを
差し替えれば、宣言を一切変えずに見た目だけを変えられる（CSSの:root差し替えに相当）。

Waffle側の語彙（Document/Schema等）は一切知らない。Waffle側から使うときは、
この核の外に変換アダプタを置き、Waffle語彙 → nodes/edges/groups の一般名詞
へ変換してから render_figure() を呼ぶこと。
"""
from . import (  # noqa: F401,E501
    shapes, shapes_decor, shapes_freeform, shapes_hex, shapes_interaction, shapes_quantity, shapes_table, shapes_titled,
)
from .canvas import render_canvas
from .radial import layout_radial
from .tree import layout_tree
from .compose import render_chart, render_figure
from .registry import known_kinds
from .tokens import DEFAULT_THEME

__all__ = ["render_figure", "render_chart", "render_canvas", "known_kinds",
           "DEFAULT_THEME", "layout_radial", "layout_tree"]

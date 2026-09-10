#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 daidaiiro
"""図を描いて検査し、SVG として書き出す道具。

    python3 draw.py <ブレストのフォルダ>

そのフォルダの `figures.json` を読み、`figures/` へ SVG を書き出す。

盤面の色は、盤面のトークンから作ったテーマで決める ──
描いたあとに CSS で上塗りすると、色を決める場所が2つになる。

**節点と辺のデータは、ここに置かない。**それはブレストごとの中身なので、
そのブレストのフォルダが `figures.json` として持つ ── 中身のフォルダに
スクリプトを置くと、道具と中身が混ざる。ここが持つのは、描き方と検査だけである。

**SVG から読み直して組み直さないこと。**一度それをやって、辺の向きを取り違えた。
`figures.json` が正本である。
"""
from __future__ import annotations

import pathlib
import sys

# 描画そのものは外の描画エンジンが行う。ここはその呼び出しと検査に徹する。
_ENGINE = pathlib.Path(__file__).resolve().parents[4] / ".claude" / "skills" / "design-svg"
if _ENGINE.is_dir():
    sys.path.insert(0, str(_ENGINE))

from svg_engine import DEFAULT_THEME, render_figure, verify  # noqa: E402

# 盤面の :root と同じ値
BOARD_THEME = dict(DEFAULT_THEME, **{
    "color.ink": "#111d1a", "color.ink-soft": "#5b6b66", "color.ink-faint": "#5b6b66",
    "color.line": "#9fb0ab", "color.box-fill": "#e9efed", "color.box-stroke": "#ccd8d4",
    "color.accent": "#0d5c55", "color.accent-bg": "#d5e6e3",
    "color.warn": "#8f5410", "color.warn-bg": "#f0e2cd",
    "chart.axis": "#9fb0ab", "chart.grid": "#ccd8d4",
})

# 節点と辺を短く書くための助け
F = lambda i, l: {"id": i, "label": l, "role": "focus"}          # noqa: E731  強調する箱
P = lambda i, l: {"id": i, "label": l}                            # noqa: E731  ふつうの箱
E = lambda a, b, l=None: ({"from": a, "to": b, "label": l}        # noqa: E731  辺
                          if l else {"from": a, "to": b})
DASH = lambda a, b, l: {"from": a, "to": b, "label": l, "dashed": True}  # noqa: E731


def draw(figs: dict, out: pathlib.Path, theme: dict | None = None) -> int:
    """図を描き、検査を通し、SVG を書き出す。食い違いがあれば数を返す。"""
    out.mkdir(parents=True, exist_ok=True)
    bad_total = 0
    for name, spec in figs.items():
        svg = render_figure(theme=theme or BOARD_THEME, **spec)
        bad = verify.check(svg)
        bad_total += len(bad)
        (out / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"{name:12} {'ok' if not bad else bad}")
    return bad_total


if __name__ == "__main__":
    import json

    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    folder = pathlib.Path(sys.argv[1])
    data = json.loads((folder / "figures.json").read_text(encoding="utf-8"))
    raise SystemExit(draw(data, folder / "figures"))

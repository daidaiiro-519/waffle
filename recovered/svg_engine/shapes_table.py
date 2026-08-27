"""表(table)部品 ── 契約(asset-authoring-contract-for-component-svg-engines)を
実際になぞって追加した検証用の部品。

- 節点系(自分の原点(0,0)基準)として作る（契約2）
- props は headers/rows という構造だけを持ち、色・寸法は一切書かない（契約3）
- 列幅はセルの文字幅から動的に決める。固定pxにしない（契約4。spatial部品で
  固定幅が原因の不具合を踏んだのと同じ轍を踏まないため）
- テキストはhtml.escapeを通す（契約7）
- <svg>ルートタグは持たない。<g>フラグメントだけを返す（契約5）
- Waffle固有語彙(Document/Schema等)は一切知らない（契約6）
"""
from __future__ import annotations

from html import escape as _e

from .registry import ComponentResult, component
from .text import text_width


@component("table")
def table(props: dict, style: dict) -> ComponentResult:
    """見出し行つきの表。

    props: headers（[str, ...]）／rows（[[str, ...], ...]。各行はheadersと同じ列数）
    """
    headers = props["headers"]
    rows = props["rows"]
    fs = style["font.size"]
    fs_small = style["font.size-small"]
    pad_x = style["chart.table-pad-x"]
    row_h = style["chart.table-row-h"]

    col_w = []
    for c, head in enumerate(headers):
        widest = text_width(str(head), fs_small)
        for r in rows:
            widest = max(widest, text_width(str(r[c]), fs))
        col_w.append(widest + pad_x * 2)

    col_x = [sum(col_w[:c]) for c in range(len(headers))]
    w = sum(col_w)
    h = row_h * (len(rows) + 1)

    body = [f'<rect x="0" y="0" width="{w:.1f}" height="{row_h:.1f}" '
           f'fill="{style["color.accent-bg"]}"/>']
    for c, head in enumerate(headers):
        body.append(f'<text x="{col_x[c] + pad_x:.1f}" y="{row_h / 2 + fs_small * style["font.baseline-ratio"]:.1f}" '
                    f'font-family="{style["font.family"]}" font-size="{fs_small}" '
                    f'font-weight="600" fill="{style["color.accent"]}">{_e(str(head))}</text>')

    for r_idx, row in enumerate(rows):
        y = row_h * (r_idx + 1)
        body.append(f'<line x1="0" y1="{y:.1f}" x2="{w:.1f}" y2="{y:.1f}" '
                    f'stroke="{style["chart.grid"]}"/>')
        for c, cell in enumerate(row):
            body.append(f'<text x="{col_x[c] + pad_x:.1f}" y="{y + row_h / 2 + fs * style["font.baseline-ratio"]:.1f}" '
                        f'font-family="{style["font.family"]}" font-size="{fs}" '
                        f'fill="{style["color.ink"]}">{_e(str(cell))}</text>')
    body.append(f'<rect x="0.5" y="0.5" width="{w - 1:.1f}" height="{h - 1:.1f}" '
               f'fill="none" stroke="{style["color.box-stroke"]}"/>')
    return ComponentResult(svg=f'<g>{"".join(body)}</g>', width=w, height=h)

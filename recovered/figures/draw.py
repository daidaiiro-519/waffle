"""宣言から描く。入力の形は主張によらず同じ（items / links / frame）。

色と書体は要素の属性として持たせる。図だけを取り出しても正しく描け、
機械で確かめられるようにするため。ページ側のCSSがあればそちらが勝つ。
"""
from __future__ import annotations

import math
from html import escape as e

INK, SOFT, FAINT = "#171B23", "#4B5563", "#79828F"
RULE, FILL, PAPER = "#C3CAD2", "#F5F7F9", "#FFFFFF"
ACC, ACC_BG, WARN = "#16636B", "#E2EFF0", "#9A4A21"
TONE = [ACC, WARN, "#7A4368", "#8A8F98"]
FONT = "Noto Sans JP"
PAD = 18


def _svg(w, h, body):
    return (f'<svg class="f-fig" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" '
            f'height="{h:.0f}" role="img">{body}</svg>')


def _tx(x, y, s, size=12, fill=INK, anchor="middle", weight="400"):
    return (f'<text class="f-t" x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}">{e(str(s))}</text>')


def _box(x, y, w, h, label, role="plain", size=12):
    fill, stroke, ink = FILL, RULE, INK
    dash = ""
    if role == "focus":
        fill, stroke, ink = ACC_BG, ACC, ACC
    if role == "muted":
        fill, stroke, ink, dash = "none", FAINT, FAINT, ' stroke-dasharray="4 3"'
    return (f'<rect class="f-box f-box--{role}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" rx="5" fill="{fill}" stroke="{stroke}"{dash}/>'
            + _tx(x + w / 2, y + h / 2 + 4, label, size, ink,
                  weight="600" if role == "focus" else "400"))


def _line(x1, y1, x2, y2, color=RULE, width=1.2, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line class="f-line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width}"{d}/>')


def _text_w(s, size=12):
    return sum((size if ord(c) > 0x2E80 else size * 0.55) for c in str(s))


# ── 解いて描くもの（つながり・階層・包含・順序） ──────────────
def _solved(fig, direction="TB"):
    """位置を解かせる。宣言をそのまま渡し、解いた数値だけを受け取る。"""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "figs"))
    from svg_graph import render_svg

    nodes, edges, groups = [], [], []

    def walk(it, parent=None, depth=0):
        nid = it["name"]
        kids = it.get("children") or []
        if kids and fig["asserts"] == "包含":
            groups.append({"label": it["name"], "members": [k["name"] for k in kids]})
            for k in kids:
                walk(k, None, depth + 1)
            return
        nodes.append({"id": nid, "name": it["name"], "role": it.get("role", "plain")})
        if parent:
            edges.append({"from": parent, "to": nid, "label": "", "ends": "head:none"})
        for k in kids:
            walk(k, nid, depth + 1)

    for it in fig["items"]:
        walk(it)
    for lk in fig.get("links", []):
        if lk["from"] in [n["id"] for n in nodes] or True:
            edges.append({"from": lk["from"], "to": lk["to"],
                          "label": lk.get("name", ""), "ends": lk.get("ends", "head:arrow")})
    if fig["asserts"] == "順序":
        names = [i["name"] for i in fig["items"]]
        edges = [{"from": a, "to": b, "label": "", "ends": "head:arrow"}
                 for a, b in zip(names, names[1:])]
    out = {"kind": "graph", "direction": direction, "nodes": nodes, "edges": edges,
           "rankSep": 0.55, "nodeSep": 0.4}
    if groups:
        out["groups"] = groups
    return render_svg(out)


def tsunagari(fig):
    return _solved(fig, "TB")


def kaisou(fig):
    return _solved(fig, "TB")


def hougan(fig):
    return _solved(fig, "TB")


def junjo(fig):
    return _solved(fig, "LR")
"""意味の型ごとの描画 ── 出すのはHTMLだけ。SVGも座標も使わない。

段と段内の位置は口から整数で受け取り、そのまま CSS grid の行と列にする。
位置をpxで書く場所は、この中に一つも無い。
"""
from __future__ import annotations

from html import escape as e

from port import arrange

# ── 点と線の図（口を通る） ─────────────────────────────


def _cell(node, placed, kind="node"):
    r, o = placed["rank"], placed["order"]
    return f'grid-row:{2 * r + 1};grid-column:{o + 1};'


def _wire_segments(src, dst, back):
    """辺を、段と列の整数だけで折れ線の断片へ分ける。"""
    r1, o1 = src["rank"], src["order"]
    r2, o2 = dst["rank"], dst["order"]
    gap = 2 * min(r1, r2) + 2 if r2 > r1 else 2 * r1 + 2
    lo, hi = min(o1, o2), max(o1, o2)
    segs = [("v", gap, o1, o1), ("v", gap, o2, o2)]
    if o1 != o2:
        segs.append(("h", gap, lo, hi))
    return [(k, row, a, b, back) for k, row, a, b in segs]


def graph(fig):
    """包含・順序・遷移・対応 ── 点と線で示すもの。"""
    nodes = [n["id"] for n in fig["nodes"]]
    edges = [(x["from"], x["to"]) for x in fig.get("edges", [])]
    groups = [g["members"] for g in fig.get("groups", [])]
    placed = arrange(nodes, edges, groups)

    cols = max(p["order"] for p in placed.values()) + 1
    rows = 2 * (max(p["rank"] for p in placed.values()) + 1)

    parts = []
    for n in fig["nodes"]:
        p = placed[n["id"]]
        role = n.get("role", "plain")
        sub = f'<span class="b__sub">{e(n["sub"])}</span>' if n.get("sub") else ""
        rows_ = "".join(f'<span class="b__row">{e(r)}</span>' for r in n.get("rows", []))
        parts.append(
            f'<div class="b b--{role}" style="{_cell(n, p)}">'
            f'<span class="b__name">{e(n["name"])}</span>{sub}{rows_}</div>')

    for x in fig.get("edges", []):
        s, d = placed[x["from"]], placed[x["to"]]
        back = d["rank"] <= s["rank"]
        for kind, row, a, b, bk in _wire_segments(s, d, back):
            cls = "w w--back" if bk else "w"
            if kind == "v":
                parts.append(f'<i class="{cls} w--v" style="grid-row:{row};grid-column:{a + 1};"></i>')
            else:
                parts.append(f'<i class="{cls} w--h" style="grid-row:{row};grid-column:{a + 1}/{b + 2};"></i>')
        if x.get("label"):
            mid = (s["order"] + d["order"]) // 2
            parts.append(f'<span class="w__label" style="grid-row:{2 * min(s["rank"], d["rank"]) + 2};'
                         f'grid-column:{mid + 1};">{e(x["label"])}</span>')

    style = f'--cols:{cols};--rows:{rows};'
    return f'<div class="graph" style="{style}">{"".join(parts)}</div>'


# ── 並べるだけの図（口を通らない） ─────────────────────


def comparison(fig):
    """対比 ── 変更前と変更後を並べる器。中身は差し替えられる。"""
    sides = []
    for side in fig["sides"]:
        body = []
        for g in side["groups"]:
            inner = INNER[g["contentKind"]](g["content"])
            label = f'<span class="frame__label">{e(g["label"])}</span>' if g.get("label") else ""
            body.append(f'<div class="frame frame--{g["contentKind"]}">{label}{inner}</div>')
        for link in side.get("links", []):
            body.insert(1, f'<div class="link"><span>{e(link["label"])}</span><i></i></div>')
        note = f'<p class="panel__note">{e(side["note"])}</p>' if side.get("note") else ""
        sides.append(f'<div class="panel panel--{side["at"]}">'
                     f'<span class="panel__label">{e(side["label"])}</span>'
                     f'<div class="panel__body">{"".join(body)}</div>{note}</div>')
    return f'<div class="cmp">{"".join(sides)}</div>'


def tree(node):
    """包含 ── 入れ子。線は親子関係から部品が置く。"""
    kids = node.get("children") or []
    box = f'<div class="b b--{node.get("role", "plain")}">{e(node["name"])}</div>'
    if not kids:
        return f'<div class="tr">{box}</div>'
    limbs = "".join(f'<div class="limb"><i class="tw tw--drop"></i><i class="tw tw--bar"></i>'
                    f"{tree(k)}</div>" for k in kids)
    return f'<div class="tr">{box}<div class="kids"><i class="tw tw--stem"></i>{limbs}</div></div>'


def transcript(t):
    """操作と、返ってきたもの。"""
    lines = "".join(f'<span class="ln ln--{l["kind"]}">{e(l["text"])}</span>' for l in t["lines"])
    return (f'<div class="win"><div class="win__bar"><i class="win__dots"></i>'
            f'<span>{e(t["title"])}</span></div><pre class="win__body">{lines}</pre></div>')


def listing(l):
    """並びと、増えた・減った。"""
    items = "".join(f'<li class="it it--{i.get("role", "unchanged")}">{e(i["name"])}</li>'
                    for i in l["items"])
    return f'<ul class="ls">{items}</ul>'


def lanes(fig):
    """帯 ── 時間順・日程・体験・枝分かれ。位置は割合で置く。"""
    total = fig.get("span", 10)
    rows = []
    for r in fig["rows"]:
        bars = "".join(
            f'<i class="bar bar--{b.get("tone", "plain")}" '
            f'style="grid-column:{b["from"] + 1}/{b["to"] + 1};">'
            f'<span>{e(b.get("label", ""))}</span></i>' for b in r["bars"])
        rows.append(f'<div class="lane"><span class="lane__name">{e(r["name"])}</span>'
                    f'<div class="lane__track" style="--span:{total};">{bars}</div></div>')
    return f'<div class="lanes">{"".join(rows)}</div>'


def amounts(fig):
    """量 ── 比率と大小。"""
    total = sum(s["value"] for s in fig["slices"]) or 1
    acc, stops = 0.0, []
    for i, s in enumerate(fig["slices"]):
        start = acc / total * 100
        acc += s["value"]
        stops.append(f'var(--tone-{i % 4}) {start:.2f}% {acc / total * 100:.2f}%')
    legend = "".join(
        f'<div class="am__row"><i class="am__chip" style="background:var(--tone-{i % 4})"></i>'
        f'<span>{e(s["name"])}</span><b>{s["value"]}</b>'
        f'<i class="am__bar" style="width:{s["value"] / total * 100:.1f}%;'
        f'background:var(--tone-{i % 4})"></i></div>'
        for i, s in enumerate(fig["slices"]))
    ring = (f'<div class="am__ring" style="background:conic-gradient({", ".join(stops)})">'
            f'<span>{e(fig.get("centre", ""))}</span></div>') if fig.get("ring") else ""
    return f'<div class="am">{ring}<div class="am__list">{legend}</div></div>'


def matrix(fig):
    """分類 ── 2つの軸のどこに位置するか。割合で置く。"""
    pts = "".join(
        f'<span class="pt" style="left:{p["x"] * 100:.1f}%;bottom:{p["y"] * 100:.1f}%;">'
        f'{e(p["name"])}</span>' for p in fig["points"])
    q = "".join(f'<span class="mx__q mx__q--{i}">{e(n)}</span>'
                for i, n in enumerate(fig.get("quadrants", [])))
    return (f'<div class="mx"><span class="mx__y">{e(fig["y"])}</span>'
            f'<div class="mx__plot">{q}{pts}</div>'
            f'<span class="mx__x">{e(fig["x"])}</span></div>')


def exchange(fig):
    """やり取りの順序 ── 参加者が列、やり取りが行。格子で置く。"""
    who = fig["participants"]
    idx = {w: i for i, w in enumerate(who)}
    heads = "".join(f'<div class="ex__who" style="grid-column:{i + 1};grid-row:1;">{e(w)}</div>'
                    for i, w in enumerate(who))
    lifes = "".join(f'<i class="ex__life" style="grid-column:{i + 1};grid-row:2/{len(fig["steps"]) + 3};"></i>'
                    for i in range(len(who)))
    rows = []
    for r, s in enumerate(fig["steps"], start=2):
        if s["kind"] == "note":
            rows.append(f'<div class="ex__note" style="grid-row:{r};grid-column:1/{len(who) + 1};">'
                        f'{e(s["text"])}</div>')
            continue
        a, b = idx[s["from"]], idx[s["to"]]
        lo, hi = min(a, b), max(a, b)
        rows.append(f'<div class="ex__msg ex__msg--{s["kind"]} '
                    f'{"ex__msg--rtl" if b < a else ""}" '
                    f'style="grid-row:{r};grid-column:{lo + 1}/{hi + 2};">'
                    f'<span>{e(s["text"])}</span></div>')
    return (f'<div class="ex" style="--who:{len(who)};">{heads}{lifes}{"".join(rows)}</div>')


def blocks(fig):
    """箱組み ── 格子に並べるだけ。"""
    cells = "".join(f'<div class="bk bk--{c.get("tone", "plain")}" '
                    f'style="grid-column:span {c.get("span", 1)};">{e(c["name"])}</div>'
                    for c in fig["cells"])
    return f'<div class="bks" style="--cols:{fig.get("cols", 3)};">{cells}</div>'


INNER = {"tree": tree, "transcript": transcript, "listing": listing}
KINDS = {"graph": graph, "comparison": comparison, "lanes": lanes, "amounts": amounts,
         "matrix": matrix, "exchange": exchange, "blocks": blocks,
         "tree": lambda f: tree(f["root"]), "transcript": lambda f: transcript(f),
         "listing": lambda f: listing(f)}


def render(fig):
    return KINDS[fig["kind"]](fig)

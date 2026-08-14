"""comparison を器と中身に分ける。

器は「変更前と変更後を並べて、何が変わったかを見せる」ことだけを担う。
中身が木に固定されていると、木でない比較に使えない。
"""
from html import escape as e

ROLES = ("unchanged", "focus", "added", "removed", "changed")


# ── 中身の部品 ────────────────────────────────────
def _box(node):
    return f'<div class="box box--{node.get("role", "unchanged")}">{e(node["name"])}</div>'


def render_tree(node):
    kids = node.get("children") or []
    if not kids:
        return f'<div class="tree">{_box(node)}</div>'
    limbs = "".join(
        '<div class="limb"><span class="wire wire--drop"></span>'
        '<span class="wire wire--bar"></span>' + render_tree(k) + "</div>" for k in kids)
    return (f'<div class="tree">{_box(node)}'
            f'<div class="kids"><span class="wire wire--stem"></span>{limbs}</div></div>')


def render_transcript(t):
    lines = "".join(f'<span class="line line--{ln["kind"]}">{e(ln["text"])}</span>'
                    for ln in t["lines"])
    return (f'<div class="win"><div class="win__bar"><span class="win__dots"></span>'
            f'<span class="win__title">{e(t["title"])}</span></div>'
            f'<pre class="win__body">{lines}</pre></div>')


def render_listing(l):
    items = "".join(f'<li class="item item--{i.get("role","unchanged")}">{e(i["name"])}</li>'
                    for i in l["items"])
    return f'<ul class="listing">{items}</ul>'


INNER = {"tree": render_tree, "transcript": render_transcript, "listing": render_listing}


# ── 器 ───────────────────────────────────────────
def render_comparison(fig):
    """変更前と変更後を並べる。中身が何であるかは知らない。"""
    sides = []
    for side in fig["sides"]:
        blocks = []
        for g in side["groups"]:
            kind = g["contentKind"]
            body = INNER[kind](g["content"])
            label = (f'<span class="frame__label">{e(g["label"])}</span>' if g.get("label") else "")
            blocks.append(f'<div class="frame frame--{kind}">{label}{body}</div>')
        for link in side.get("links") or []:
            blocks.insert(1, f'<div class="link"><span class="link__label">'
                             f'{e(link["label"])}</span><span class="link__line"></span></div>')
        reading = side.get("reading")
        sides.append(
            f'<div class="panel panel--{side["at"]}">'
            f'<span class="panel__label">{e(side["label"])}</span>'
            f'<div class="panel__body">{"".join(blocks)}</div>'
            + (f'<p class="panel__reading">{e(reading)}</p>' if reading else "") + "</div>")
    return (f'<figure class="fig fig--comparison">'
            f'<div class="fig__sides">{"".join(sides)}</div>'
            f'<figcaption>{e(fig["intent"])}</figcaption></figure>')
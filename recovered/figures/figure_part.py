"""図の部品 ── 構造化データをHTMLの骨組みへ写す。

見た目は一切持たない。持つのは「何であるか」を класс名へ写す対応だけで、
どう見えるかは CSS 側にある。ここに色や大きさが現れたら、それは
データと見た目の分離が壊れた合図。
"""
from html import escape as e


def _box(node):
    role = node.get("role", "plain")
    return f'<div class="box box--{role}">{e(node["name"])}</div>'


def _tree(node):
    kids = node.get("children") or []
    if not kids:
        return f'<div class="tree">{_box(node)}</div>'
    limbs = "".join(
        f'<div class="limb">'
        f'<span class="wire wire--drop"></span><span class="wire wire--bar"></span>'
        f'{_tree(k)}</div>'
        for k in kids
    )
    return (f'<div class="tree">{_box(node)}'
            f'<div class="kids"><span class="wire wire--stem"></span>{limbs}</div></div>')


def _group(group):
    return (f'<div class="frame">'
            f'<span class="frame__label">{e(group["label"])}</span>'
            f'{_tree(group["tree"])}</div>')


def _link(link):
    return (f'<div class="link">'
            f'<span class="link__label">{e(link["label"])}</span>'
            f'<span class="link__line"></span></div>')


def _side(side):
    body = [_group(g) for g in side["groups"]]
    for link in side.get("links") or []:
        body.insert(1, _link(link))          # 囲みと囲みの間に置く
    reading = side.get("reading")
    return (f'<div class="panel panel--{side["at"]}">'
            f'<span class="panel__label">{e(side["label"])}</span>'
            f'<div class="panel__body">{"".join(body)}</div>'
            + (f'<p class="panel__reading">{e(reading)}</p>' if reading else "")
            + "</div>")


def render_structure(figure):
    return (f'<figure class="fig fig--structure">'
            f'<div class="fig__sides">{"".join(_side(s) for s in figure["sides"])}</div>'
            f'<figcaption>{e(figure["intent"])}</figcaption></figure>')
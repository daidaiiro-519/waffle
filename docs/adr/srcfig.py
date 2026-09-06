"""出典の原則を見せる図。

配色は呼ぶ側の CSS 変数に合わせる ── 頁と盤面で変数名が違うため、
同じ図を2度描かずに、palette だけを差し替える。
"""

PAGE = dict(id="p", card="--card", line="--line", ink="--ink",
            muted="--muted", accent="--accent")
BOARD = dict(id="b", card="--panel", line="--key", ink="--ink",
             muted="--muted", accent="--add")


def _box(P, x, y, w, h, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
            f'fill="var({P["card"]})" stroke="var({P["line"]})" '
            f'stroke-width="1.4"{d}/>')


def _t(P, x, y, s, size=13, weight="600", role="ink"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="var({P[role]})" text-anchor="middle" '
            f'font-family="system-ui,sans-serif">{s}</text>')


def _line(P, x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="var({P["line"]})" stroke-width="1.4" '
            f'marker-end="url(#ar{P["id"]})"/>')


def _defs(P):
    return (f'<defs><marker id="ar{P["id"]}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="var({P["line"]})"/></marker></defs>')


def one(P):
    """規則1件に原典1本。2本目が欲しくなったときの2つの出口。"""
    svg = ('<svg viewBox="0 0 820 200" xmlns="http://www.w3.org/2000/svg">' + _defs(P)
           + _box(P, 60, 30, 180, 45) + _box(P, 360, 30, 180, 45)
           + _t(P, 150, 58, "規則 1件") + _t(P, 450, 58, "原典 1本")
           + _line(P, 240, 52, 360, 52)
           + _t(P, 300, 24, "支える", 11, "500", "muted")
           + _t(P, 410, 100, "2本目が欲しくなったときは", 12, "700", "accent")
           + _box(P, 60, 115, 320, 58, True) + _box(P, 430, 115, 330, 58, True)
           + _t(P, 220, 138, "命題が2つ入っている", 12)
           + _t(P, 220, 160, "規則を2件に割る", 12, "700", "accent")
           + _t(P, 595, 138, "どれも言い切っていない", 12)
           + _t(P, 595, 160, "規則にしない。委譲へ移す", 12, "700", "accent")
           + '</svg>')
    return (svg, "原典は1本。2本目が欲しくなるのは、規則の切り方が合っていない合図である")


def fall(P):
    """照合が落ちたときの分岐。"""
    svg = ('<svg viewBox="0 0 820 180" xmlns="http://www.w3.org/2000/svg">' + _defs(P)
           + _box(P, 25, 68, 160, 40) + _t(P, 105, 93, "照合が落ちた")
           + _line(P, 185, 88, 245, 88)
           + _box(P, 245, 68, 180, 40) + _t(P, 335, 93, "原典を読む")
           + _line(P, 425, 82, 485, 48) + _line(P, 425, 96, 485, 128)
           + _box(P, 485, 20, 305, 52) + _box(P, 485, 104, 305, 52)
           + _t(P, 637, 42, "その考えが、まだ在る")
           + _t(P, 637, 62, "指し直す。規則は変えない", 11, "500", "muted")
           + _t(P, 637, 126, "その考えが、無い")
           + _t(P, 637, 146, "その規則は出典を失っている", 11, "500", "accent")
           + '</svg>')
    return (svg, "照合が落ちても、規則が出典を失ったとは限らない。落ちたのは指し先である")


ONE = one(PAGE)
FALL = fall(PAGE)
ONE_B = one(BOARD)
FALL_B = fall(BOARD)

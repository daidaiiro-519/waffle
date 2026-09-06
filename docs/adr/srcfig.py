"""出典の原則を見せる図。"""


def _box(x, y, w, h, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="var(--card)" '
            f'stroke="var({"--rule" if dash else "--line"})" stroke-width="1.4"{d}/>')


def _t(x, y, s, size=13, weight="600", fill="--ink"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="var({fill})" text-anchor="middle" '
            f'font-family="system-ui,sans-serif">{s}</text>')


def _line(x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--line)" '
            f'stroke-width="1.4" marker-end="url(#ar)"/>')


DEFS = ('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--line)"/>'
        '</marker></defs>')

_ONE = ('<svg viewBox="0 0 820 200" xmlns="http://www.w3.org/2000/svg">' + DEFS
        + _box(60, 30, 180, 45) + _box(360, 30, 180, 45)
        + _t(150, 58, "規則 1件") + _t(450, 58, "原典 1本")
        + _line(240, 52, 360, 52)
        + _t(300, 24, "支える", 11, "500", "--muted")
        + _t(410, 100, "2本目が欲しくなったときは", 12, "700", "--accent")
        + _box(60, 115, 320, 58, True) + _box(430, 115, 330, 58, True)
        + _t(220, 138, "命題が2つ入っている", 12)
        + _t(220, 160, "規則を2件に割る", 12, "700", "--accent")
        + _t(595, 138, "どれも言い切っていない", 12)
        + _t(595, 160, "規則にしない。委譲へ移す", 12, "700", "--accent")
        + '</svg>')
ONE = (_ONE, "原典は1本。2本目が欲しくなるのは、規則の切り方が合っていない合図である")

_FALL = ('<svg viewBox="0 0 820 180" xmlns="http://www.w3.org/2000/svg">' + DEFS
         + _box(25, 68, 160, 40) + _t(105, 93, "照合が落ちた")
         + _line(185, 88, 245, 88)
         + _box(245, 68, 180, 40) + _t(335, 93, "原典を読む")
         + _line(425, 82, 485, 48) + _line(425, 96, 485, 128)
         + _box(485, 20, 305, 52) + _box(485, 104, 305, 52)
         + _t(637, 42, "その考えが、まだ在る")
         + _t(637, 62, "指し直す。規則は変えない", 11, "500", "--muted")
         + _t(637, 126, "その考えが、無い")
         + _t(637, 146, "その規則は出典を失っている", 11, "500", "--accent")
         + '</svg>')
FALL = (_FALL, "照合が落ちても、規則が出典を失ったとは限らない。落ちたのは指し先である")

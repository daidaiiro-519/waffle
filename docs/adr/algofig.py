"""検査の組み方を見せる図。"""


def _box(x, y, w, h, dash=False, fill="#fff"):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" '
            f'stroke="{"#c3c8d0" if dash else "#8b93a1"}" stroke-width="1.4"{d}/>')


def _t(x, y, s, size=12, weight="600", fill="#1c2530"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="middle" '
            f'font-family="system-ui,sans-serif">{s}</text>')


def _h(x1, x2, y, dash=False):
    d = ' stroke-dasharray="4 4"' if dash else ""
    return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#8b93a1" '
            f'stroke-width="1.4" marker-end="url(#a)"{d}/>')


def _v(x, y1, y2, dash=False):
    d = ' stroke-dasharray="4 4"' if dash else ""
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#8b93a1" '
            f'stroke-width="1.4" marker-end="url(#a)"{d}/>')


DEFS = ('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#8b93a1"/>'
        '</marker></defs>')

# ── 1枚目: 検査が宣言を出典として持つ
_G = ('<svg viewBox="0 0 830 230" xmlns="http://www.w3.org/2000/svg" '
      'style="width:100%;height:auto">' + DEFS
      + _box(30, 70, 200, 70) + _box(320, 70, 200, 70) + _box(590, 70, 210, 70)
      + _t(130, 98, "宣言", 13) + _t(130, 120, "references/authoring.md", 10, "400", "#5a6472")
      + _t(420, 98, "Check", 13) + _t(420, 120, "declared_in ・ needle", 10, "400", "#5a6472")
      + _t(695, 98, "規約", 13) + _t(695, 120, "constraints/*.md", 10, "400", "#5a6472")
      + _h(230, 320, 105) + _h(520, 590, 105)
      + _t(275, 58, "文字列が実在するか", 10, "500", "#5a6472")
      + _t(555, 58, "規約を見る", 10, "500", "#5a6472")
      + _v(130, 140, 180, True) + _v(420, 140, 180, True) + _v(695, 140, 180, True)
      + _t(130, 200, "消すと、検査が落ちる", 12, "600", "#a8452f")
      + _t(420, 200, "needle が無いと登録できない", 12)
      + _t(695, 200, "食い違いを出す", 12)
      + '</svg>')
GUARD = (_G, "検査が、守っている宣言を出典として持つ ── 規則と同じ形にする")

# ── 2枚目: 読み取りを1か所へ畳む
_R = ('<svg viewBox="0 0 830 410" xmlns="http://www.w3.org/2000/svg" '
      'style="width:100%;height:auto">' + DEFS
      + _t(415, 30, "いま ── 検査がそれぞれ本文を撫でる", 13)
      + _box(40, 45, 130, 30) + _box(40, 85, 130, 30) + _box(40, 125, 130, 30)
      + _t(105, 64, "規則の ID") + _t(105, 104, "照合する文字列") + _t(105, 144, "層の種類")
      + _box(330, 45, 170, 110, False, "#f6f7f9")
      + _t(415, 104, "規約の本文", 13)
      + _h(170, 330, 60) + _h(170, 330, 100) + _h(170, 330, 140)
      + _t(415, 185, "正規表現が5か所に散る ── 1つずつ壊れる", 11, "500", "#a8452f")
      + _t(415, 225, "設計後 ── 読み取りは1か所", 13)
      + _box(40, 240, 130, 30) + _box(40, 280, 130, 30) + _box(40, 320, 130, 30)
      + _t(105, 259, "規則の ID") + _t(105, 299, "照合する文字列") + _t(105, 339, "層の種類")
      + _box(250, 240, 150, 110)
      + _t(325, 285, "tables()") + _t(325, 305, "sections()")
      + _box(460, 240, 170, 110, False, "#f6f7f9")
      + _t(545, 294, "規約の本文", 13)
      + _h(170, 250, 255) + _h(170, 250, 295) + _h(170, 250, 335) + _h(400, 460, 295)
      + _t(415, 390, "列名で読む ── ID の形にもバッククォートにも依存しない", 11, "500", "#5a6472")
      + '</svg>')
READ = (_R, "検査ごとの正規表現をやめ、表を列名で読む層を1つだけ置く")

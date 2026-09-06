"""保守対象ごとの契約を1枚で見せる図。"""

def _box(x, w, y, h, cls="b"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
            f'fill="{"#f6f7f9" if cls=="g" else "#fff"}" stroke="{"#c3c8d0" if cls=="g" else "#8b93a1"}" '
            f'stroke-width="{1 if cls=="g" else 1.4}"'
            f'{" stroke-dasharray=\"5 4\"" if cls=="g" else ""}/>')

def _t(x, y, s, size=13, weight="600", fill="#1c2530"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="middle" font-family="system-ui,sans-serif">{s}</text>')

def _arrow(x, y1, y2):
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="#8b93a1" '
            f'stroke-width="1.4" marker-end="url(#ah)"/>')

_SVG = ('<svg viewBox="0 0 830 275" xmlns="http://www.w3.org/2000/svg" '
    'style="width:100%;height:auto">'
    '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
    'markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#8b93a1"/></marker></defs>'
    # 群
    + _box(20, 450, 45, 150, "g") + _box(490, 150, 45, 150, "g") + _box(660, 150, 45, 150, "g")
    + _t(245, 68, "保守する ── 文言で照合できる")
    + _t(565, 68, "振る舞いを持つ")
    + _t(735, 68, "原典 ── SSOT")
    # 中身
    + _box(35, 130, 95, 50) + _box(180, 130, 95, 50) + _box(325, 130, 95, 50)
    + _box(505, 120, 95, 50) + _box(675, 120, 95, 50)
    + _t(100, 118, "constraints") + _t(100, 136, "規約の実物", 11, "400", "#5a6472")
    + _t(245, 118, "references") + _t(245, 136, "定義と手順", 11, "400", "#5a6472")
    + _t(390, 118, "templates") + _t(390, 136, "実物の型", 11, "400", "#5a6472")
    + _t(565, 118, "scripts") + _t(565, 136, "機械", 11, "400", "#5a6472")
    + _t(735, 118, "sources") + _t(735, 136, "原文", 11, "400", "#5a6472")
    # 誰が確かめるか
    + _arrow(245, 200, 222) + _arrow(565, 200, 222) + _arrow(735, 200, 222)
    + _t(245, 240, "check.py が見る")
    + _t(565, 240, "テストが見る")
    + _t(735, 240, "契約を持たない", 13, "600", "#8b93a1")
    + '</svg>')

CONTRACT = (_SVG, "保守するものだけが契約を持つ。原典は契約を持たない ── 変えないためである")
FIGS = [CONTRACT]

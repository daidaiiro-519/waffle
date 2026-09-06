def _b(x, y, w, h, label, stroke, sw=1.3, size=8.5, ly=None, bold=False):
    fw = ' font-weight="700"' if bold else ""
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" stroke="{stroke}" stroke-width="{sw}"/>'
    if label:
        out += (f'<text x="{x + w/2}" y="{y + (ly or h/2 + 3.5)}" text-anchor="middle" '
                f'font-size="{size}" fill="{stroke}"{fw}>{label}</text>')
    return out

def _t(x, y, s, tone="var(--muted)", size=8.5, anchor=None, bold=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    fw = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"

ONEWAY = ('<svg viewBox="0 0 780 400" role="img" aria-label="入れ子や場合分けは詰まるが、並べて対応を宣言すると作りは1通りのまま3つの形が表せる">'
 + _t(20, 20, "採らない形　── どれも、どこかで詰まる", D, 10, bold=True)
 # 1) 文脈を上に入れ子
 + _b(20, 34, 230, 96, "", D, 1.2)
 + _t(135, 52, "入れ子：文脈を上に", D, 9, "middle", True)
 + _b(36, 62, 198, 22, "contexts/ 予約", M, 1)
 + _b(52, 90, 166, 20, "subdomains/ 予約管理", M, 1)
 + _t(135, 124, "1つの領域が2つの文脈に割れると入らない", D, 8, "middle")
 # 2) 領域を上に入れ子
 + _b(268, 34, 230, 96, "", D, 1.2)
 + _t(383, 52, "入れ子：領域を上に", D, 9, "middle", True)
 + _b(284, 62, 198, 22, "subdomains/ 予約管理", M, 1)
 + _b(300, 90, 166, 20, "contexts/ 予約", M, 1)
 + _t(383, 124, "1つの文脈が2つの領域をまたぐと入らない", D, 8, "middle")
 # 3) 場合分け
 + _b(516, 34, 244, 96, "", D, 1.2)
 + _t(638, 52, "場合分けする", D, 9, "middle", True)
 + _b(528, 62, 70, 22, "1対1用", M, 1, 8)
 + _b(604, 62, 70, 22, "1対多用", M, 1, 8)
 + _b(680, 62, 70, 22, "多対1用", M, 1, 8)
 + _t(638, 100, "引き方も検査も3通りになる", D, 8, "middle")
 + _t(638, 124, "作りが3つに増える", D, 8, "middle")
 + '<line x1="20" y1="150" x2="760" y2="150" stroke="var(--rule)"/>'
 + _t(20, 174, "採る形　── 並べて、対応を宣言で持つ", K, 10, bold=True)
 + _b(20, 188, 300, 150, "", K, 1.6)
 + _t(170, 208, "作りは1通り", K, 9, "middle", True)
 + _b(36, 220, 130, 26, "subdomains/", M, 1.1)
 + _b(174, 220, 130, 26, "contexts/", M, 1.1)
 + _t(170, 264, "入れ子にしない。横に並べる", M, 8, "middle")
 + _b(36, 278, 268, 44, "", A, 1.3)
 + _t(170, 296, "対応は、文書の欄で宣言する", A, 8.5, "middle", True)
 + _t(170, 312, "「この文脈が扱う領域」／「この領域が属する事業領域」", M, 8, "middle")
 + '<line x1="320" y1="262" x2="352" y2="262" stroke="var(--key)" stroke-width="1.5"/>'
 + _t(336, 254, "すると", K, 8, "middle")
 + _b(356, 188, 404, 150, "", M, 1.2)
 + _t(558, 208, "どの対応も、宣言に書いた結果として現れる", M, 9, "middle", True)
 + _b(372, 222, 120, 40, "", C, 1.1)
 + _t(432, 238, "領域1つ → 文脈1つ", C, 8.5, "middle")
 + _t(432, 253, "1対1", M, 8, "middle")
 + _b(500, 222, 120, 40, "", C, 1.1)
 + _t(560, 238, "領域1つ → 文脈2つ", C, 8.5, "middle")
 + _t(560, 253, "課題ごとに別のモデル", M, 8, "middle")
 + _b(628, 222, 120, 40, "", C, 1.1)
 + _t(688, 238, "領域2つ → 文脈1つ", C, 8.5, "middle")
 + _t(688, 253, "1つの文脈で開発する", M, 8, "middle")
 + _t(558, 288, "schema は1つ　／　引き方は1つ　／　検査は1つ", K, 9, "middle", True)
 + _t(558, 310, "対応の形が増えても、作りは増えない", M, 8, "middle")
 + '<line x1="20" y1="356" x2="760" y2="356" stroke="var(--rule)"/>'
 + _t(20, 376, "「3つに対応する」は、3通りの作りを持つことではない ── 1通りの作りで、3つの形が書けるということ", K, 9, bold=True)
 + '</svg>',
 '<b>入れ子にすると、作りは1通りでも表せない形が出る。</b>場合分けすると、引き方も検査も3通りになる。'
 '<b>並べて対応を宣言すれば、作りは1通りのまま、どの対応もその宣言の中に現れる</b> ── '
 'schema も引き方も検査も1つで済み、対応の形が増えても作りは増えない。')

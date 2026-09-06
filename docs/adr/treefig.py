def _box(x, y, w, h, label, stroke, sw=1.3, fill="none", lx=8, ly=15, size=9, bold=True):
    fw = ' font-weight="700"' if bold else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
            f'<text x="{x + lx}" y="{y + ly}" font-size="{size}" fill="{stroke}"{fw}>{label}</text>')

def _f(x, y, name, tone="currentColor", size=8.5):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}">{name}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"

TREE = ('<svg viewBox="0 0 780 400" role="img" aria-label="業務でフォルダを切ると入れ子になり、層でフォルダを切ると同じ業務が兄弟に散る">'
 '<text x="20" y="20" font-size="10.5" font-weight="700" fill="var(--key)">B　業務でフォルダを切る　── 入れ子になる</text>'
 + _box(20, 30, 380, 286, "specs/", M, 1.2)
 + _box(32, 50, 356, 218, "予約/　── 文脈1つ", K, 1.6)
 + _f(46, 88, "context.json") + _f(200, 88, "境界と、その中の言葉", M)
 + _f(46, 106, "model.予約.json") + _f(200, 106, "一貫性の境界ごと", M)
 + _f(46, 124, "operation.確定する.json") + _f(200, 124, "呼べる操作ごと", M)
 + _f(46, 142, "operation.取り消す.json")
 + _box(44, 156, 164, 46, "interface.cli/", A, 1.3, "none", 8, 14, 8.5)
 + _f(54, 190, "offer.確定する.json")
 + _box(216, 156, 160, 46, "interface.mcp/", A, 1.3, "none", 8, 14, 8.5)
 + _f(226, 190, "offer.確定する.json")
 + _box(44, 208, 164, 52, "interface.ui/", A, 1.3, "none", 8, 14, 8.5)
 + _f(54, 240, "offer.予約画面.json") + _f(54, 254, "flow.申し込み.json")
 + _box(216, 208, 160, 52, "platform.保存/", A, 1.3, "none", 8, 14, 8.5)
 + _f(226, 240, "requirement.json") + _f(226, 254, "指標と目標", M)
 + _f(44, 288, "integration.予約-請求.json", A) + _f(215, 288, "文脈をまたぐ", M)
 + _f(44, 306, "area.json", A) + _f(215, 306, "領域（中核 ・ 一般 ・ 補完）", M)
 + '<text x="420" y="20" font-size="10.5" font-weight="700" fill="var(--muted)">A　層でフォルダを切る　── 兄弟が並ぶ</text>'
 + _box(420, 30, 340, 286, "specs/", M, 1.2)
 + "".join(
     _box(432, 50 + i * 42, 316, 34, lbl, D if "予約" in lbl else M, 1.1, "none", 8, 14, 8.5)
     + _f(444, 50 + i * 42 + 28, sub, M)
     for i, (lbl, sub) in enumerate([
         ("domain.予約/", "context.json ・ model.*.json ・ operation.*.json"),
         ("domain.予約+interface.cli/", "offer.確定する.json"),
         ("domain.予約+interface.mcp/", "offer.確定する.json"),
         ("domain.予約+interface.ui/", "offer.予約画面.json ・ flow.申し込み.json"),
         ("domain.予約+platform.保存/", "requirement.json"),
         ("domain.請求/", "…"),
     ]))
 + _f(432, 310, "同じ業務（予約）が、6つのうち5つの名前に現れる ── 文書は兄弟に散る", D)
 + '<line x1="20" y1="330" x2="760" y2="330" stroke="var(--rule)"/>'
 + _f(20, 350, "B は「この業務の全部」が1つの箱に入る。A は「全部の CLI の約束」が1か所に集まる", M, 9)
 + _f(20, 368, "どちらを選んでも、片方は横断になる ── 違うのは、横断を人がするか、引き方がするかである", M, 9)
 + '<text x="20" y="390" font-size="9" fill="var(--key)">人が読む単位は業務である（論点2 ・ 論点15）── '
 '<tspan font-weight="700">人の側を1つにまとめ、横断は引き方に任せる</tspan></text>'
 '</svg>',
 '<b>業務 × 接点の文書は、実際に作る。</b>数は「その文脈を、その接点で差し出す能力の数」だけである。'
 '<b>業務でフォルダを切ると、接点と基盤の層がその中に入れ子で収まる。</b>'
 '層でフォルダを切ると、同じ業務の名前が兄弟のフォルダに繰り返し現れ、文書が散る。')

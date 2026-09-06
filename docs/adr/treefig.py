def _box(x, y, w, h, label, stroke, sw=1.3, lx=8, ly=15, size=9, bold=True, note=None):
    fw = ' font-weight="700"' if bold else ""
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" '
           f'stroke="{stroke}" stroke-width="{sw}"/>'
           f'<text x="{x + lx}" y="{y + ly}" font-size="{size}" fill="{stroke}"{fw}>{label}</text>')
    if note:
        out += (f'<text x="{x + w - 8}" y="{y + ly}" text-anchor="end" font-size="8" '
                f'fill="var(--muted)">{note}</text>')
    return out

def _f(x, y, name, tone="currentColor", size=8.5):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}">{name}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"

TREE = ('<svg viewBox="0 0 780 430" role="img" aria-label="フォルダは何を入れるかを名乗り、実体の名前はその中に置く">'
 '<text x="20" y="20" font-size="10.5" font-weight="700" fill="var(--key)">B　業務でフォルダを切る</text>'
 + _box(20, 30, 440, 344, "specs/", M, 1.2)
 + _box(32, 50, 396, 262, "contexts/", M, 1.2, 8, 15, 9, True, "文脈ごとに1つ")
 + _box(44, 70, 372, 232, "予約/", K, 1.6, 8, 16, 9.5, True, "文脈の名前")
 + _f(58, 106, "context.json") + _f(200, 106, "境界と、その中の言葉", M)
 + _box(56, 118, 172, 56, "models/", C, 1.1, 8, 14, 8.5, True, None)
 + _f(68, 148, "一貫性の境界ごと", M, 8)
 + _f(68, 164, "予約.json", C, 8)
 + _box(240, 118, 164, 56, "operations/", C, 1.1, 8, 14, 8.5, True, None)
 + _f(252, 148, "操作ごと", M, 8)
 + _f(252, 164, "確定する.json ・ 取り消す.json", C, 8)
 + _box(56, 182, 348, 62, "interfaces/", A, 1.3, 8, 14, 8.5, True, "業務 × 接点")
 + _f(68, 212, "cli/確定する.json", C, 8) + _f(200, 212, "mcp/確定する.json", C, 8)
 + _f(68, 228, "ui/予約画面.json", C, 8) + _f(200, 228, "ui/申し込み.flow.json", C, 8)
 
 + _box(56, 252, 348, 40, "platforms/", A, 1.3, 8, 14, 8.5, True, "業務 × 基盤")
 + _f(68, 282, "保存.json　── 指標と目標", C, 8)
 + _box(32, 320, 196, 40, "integrations/", A, 1.2, 8, 14, 8.5, True, None)
 + _f(44, 350, "予約-請求.json　── 文脈どうしの連係", M, 8)
 + _box(236, 320, 192, 40, "areas/", A, 1.2, 8, 14, 8.5, True, None)
 + _f(248, 350, "予約管理.json ・ 請求.json", M, 8)
 + '<text x="480" y="20" font-size="10.5" font-weight="700" fill="var(--muted)">A　層でフォルダを切る</text>'
 + _box(480, 30, 280, 344, "specs/", M, 1.2)
 + "".join(
     _box(492, 50 + i * 44, 256, 36, lbl, D if "予約" in lbl else M, 1.1, 8, 14, 8.5)
     + _f(504, 50 + i * 44 + 29, sub, M, 8)
     for i, (lbl, sub) in enumerate([
         ("domain.予約/", "context.json ・ model.* ・ operation.*"),
         ("domain.予約+interface.cli/", "offer.確定する.json"),
         ("domain.予約+interface.mcp/", "offer.確定する.json"),
         ("domain.予約+interface.ui/", "offer.予約画面.json ・ flow.*.json"),
         ("domain.予約+platform.保存/", "requirement.json"),
         ("domain.請求/", "…"),
     ]))
 + _f(492, 338, "同じ業務の名前が、6つのうち5つに現れる", D, 8.5)
 + _f(492, 356, "── 文書が兄弟に散る", D, 8.5)
 + '<line x1="20" y1="386" x2="760" y2="378" stroke="var(--rule)"/>'
 + _f(20, 402, "フォルダは「何を入れるか」を名乗り、実体の名前はその中に置く ── contexts/ の中に 予約/ が入る", M, 9)
 + '<text x="20" y="418" font-size="9" fill="var(--key)">人が読む単位は業務である（論点2 ・ 論点15）── '
 '<tspan font-weight="700">人の側を1つにまとめ、横断は引き方に任せる</tspan></text>'
 '</svg>',
 '<b>フォルダは「何を入れるか」を名乗り、実体の名前はその中に置く。</b>'
 '<code>contexts/</code> の中に <code>予約/</code> が入り、その中で '
 '<code>models/</code> ・ <code>operations/</code> ・ <code>interfaces/</code> ・ <code>platforms/</code> に分かれる ── '
 '<b>接点と基盤の層が、業務の中に入れ子で収まる。</b>'
 '層でフォルダを切ると、同じ業務の名前が兄弟のフォルダに繰り返し現れ、文書が散る。'
 '<b>業務領域も、それぞれ1本の文書になる</b>（<code>areas/</code>）── ただし文脈との対応が1対1とは限らないので、<b>文脈の入れ子には入らず、横に並ぶ。</b>')

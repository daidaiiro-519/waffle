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
 + _box(32, 50, 416, 22, "business-domains/　　事業領域　── 分類の基準", M, 1.1, 8, 15, 8.5)
 + _box(32, 78, 416, 22, "subdomains/　　業務領域　── 中核 ・ 一般 ・ 補完と、その根拠", M, 1.1, 8, 15, 8.5)
 + _box(32, 106, 416, 244, "contexts/", M, 1.2, 8, 15, 9, True, "文脈ごとに1つ")
 + _box(44, 126, 392, 190, "予約/", K, 1.6, 8, 16, 9.5, True, "文脈の名前")
 + _f(58, 160, "context.json") + _f(210, 160, "この文脈で通じる言葉", M)
 + _box(56, 170, 182, 56, "aggregates/", C, 1.1, 8, 14, 8.5)
 + _f(68, 200, "予約.json", C, 8) + _f(68, 216, "一貫性の境界", M, 8)
 + _box(250, 170, 178, 56, "entities/ ・ values/", C, 1.1, 8, 14, 8.5)
 + _f(262, 200, "予約者.json ・ 金額.json", C, 8) + _f(262, 216, "集約の内側から出たもの", M, 8)
 + _box(56, 232, 182, 40, "usecases/ ・ services/", C, 1.1, 8, 14, 8.5)
 + _f(68, 262, "確定する.json ほか", C, 8)
 + _box(250, 232, 178, 40, "interfaces/", A, 1.3, 8, 14, 8.5)
 + _f(262, 262, "cli/確定する.json ほか", C, 8)
 + _box(56, 278, 372, 26, "platforms/　　保存.json　── 指標と目標", A, 1.3, 8, 16, 8.5)
 + _box(44, 322, 392, 22, "relationships/　　予約-請求.json　── 文脈どうしの関係", A, 1.2, 8, 15, 8.5)
 + _f(32, 366, "文脈の中の並びは、8種別（論点19）がそのまま来る", M, 8.5)
 + '<text x="480" y="20" font-size="10.5" font-weight="700" fill="var(--muted)">A　層でフォルダを切る</text>'
 + _box(480, 30, 280, 344, "specs/", M, 1.2)
 + "".join(
     _box(492, 50 + i * 44, 256, 36, lbl, D if "予約" in lbl else M, 1.1, 8, 14, 8.5)
     + _f(504, 50 + i * 44 + 29, sub, M, 8)
     for i, (lbl, sub) in enumerate([
         ("domain.予約/", "context ・ aggregate ・ usecase …"),
         ("domain.予約+interface.cli/", "offer.確定する.json"),
         ("domain.予約+interface.mcp/", "offer.確定する.json"),
         ("domain.予約+interface.ui/", "offer.*.json ・ flow.*.json"),
         ("domain.予約+platform.保存/", "requirement.json"),
         ("domain.請求/", "…"),
     ]))
 + _f(492, 338, "同じ業務の名前が、6つのうち5つに現れる", D, 8.5)
 + _f(492, 356, "── 文書が兄弟に散る", D, 8.5)
 + '<line x1="20" y1="386" x2="760" y2="386" stroke="var(--rule)"/>'
 + _f(20, 402, "フォルダは「何を入れるか」を名乗り、実体の名前はその中に置く ── contexts/ の中に 予約/ が入る", M, 9)
 + '<text x="20" y="418" font-size="9" fill="var(--key)">事業領域と業務領域は文脈の外に並ぶ（対応が1対1とは限らない）── '
 '<tspan font-weight="700">連係は contexts/ の中に置く</tspan></text>'
 '</svg>',
 '<b>フォルダは「何を入れるか」を名乗り、実体の名前はその中に置く。</b>'
 '文脈の中には、8種別（集約 ・ エンティティ ・ 値オブジェクト ・ 業務ユースケース ・ 業務サービス）と、'
 '接点 ・ 基盤の層が入れ子で収まる。'
 '<b>事業領域と業務領域は、文脈の外に並ぶ</b> ── 対応が1対1とは限らないからである。'
 '<b>文脈どうしの連係は、文脈の間にあるので <code>contexts/</code> の中に置く。</b>')

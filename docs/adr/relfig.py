def _b(x, y, w, h, label, stroke, sw=1.4, sub=None, size=9.5):
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" '
           f'stroke="{stroke}" stroke-width="{sw}"/>'
           f'<text x="{x + w/2}" y="{y + (18 if sub else h/2 + 4)}" text-anchor="middle" '
           f'font-size="{size}" fill="{stroke}">{label}</text>')
    if sub:
        out += (f'<text x="{x + w/2}" y="{y + 34}" text-anchor="middle" font-size="8" '
                f'fill="var(--muted)">{sub}</text>')
    return out

K, A, M, C = "var(--key)", "var(--add)", "var(--muted)", "currentColor"

REL = ('<svg viewBox="0 0 780 300" role="img" aria-label="業務領域と区切られた文脈の対応は、1対1にも、1対多にも、多対1にもなる">'
 '<text x="20" y="20" font-size="10" fill="var(--muted)">業務領域　── 事業方針で決まる構造（見つけるもの）</text>'
 '<text x="20" y="36" font-size="10" fill="var(--add)">区切られた文脈　── 設計判断（技術者が決めるもの）</text>'
 '<line x1="20" y1="46" x2="760" y2="46" stroke="var(--rule)"/>'
 '<text x="20" y="70" font-size="9.5" font-weight="700" fill="currentColor">① 1対1</text>'
 + _b(20, 80, 200, 34, "業務領域　予約管理", M, 1.2)
 + _b(20, 126, 200, 34, "文脈　予約", A, 1.6)
 + '<line x1="120" y1="114" x2="120" y2="122" stroke="var(--soft)" stroke-width="1.2"/>'
 + '<text x="20" y="182" font-size="8.5" fill="var(--muted)">いちばん分かりやすい形。</text>'
 + '<text x="20" y="196" font-size="8.5" fill="var(--muted)">ただし、これは定義ではない</text>'
 + '<text x="270" y="70" font-size="9.5" font-weight="700" fill="currentColor">② 1つの領域に、複数の文脈</text>'
 + _b(270, 80, 220, 34, "業務領域　予約管理", M, 1.2)
 + _b(270, 126, 104, 34, "文脈　予約", A, 1.6)
 + _b(386, 126, 104, 34, "文脈　空き状況", A, 1.6)
 + '<line x1="322" y1="114" x2="322" y2="122" stroke="var(--soft)" stroke-width="1.2"/>'
 + '<line x1="438" y1="114" x2="438" y2="122" stroke="var(--soft)" stroke-width="1.2"/>'
 + '<text x="270" y="182" font-size="8.5" fill="var(--muted)">一つの業務領域でも課題が複数あれば、</text>'
 + '<text x="270" y="196" font-size="8.5" fill="var(--muted)">課題ごとに別のモデルを作るほうがよい</text>'
 + '<text x="540" y="70" font-size="9.5" font-weight="700" fill="currentColor">③ 1つの文脈に、複数の領域</text>'
 + _b(540, 80, 104, 34, "領域　予約管理", M, 1.2)
 + _b(656, 80, 104, 34, "領域　請求", M, 1.2)
 + _b(540, 126, 220, 34, "文脈　注文まわり", A, 1.6)
 + '<line x1="592" y1="114" x2="592" y2="122" stroke="var(--soft)" stroke-width="1.2"/>'
 + '<line x1="708" y1="114" x2="708" y2="122" stroke="var(--soft)" stroke-width="1.2"/>'
 + '<text x="540" y="182" font-size="8.5" fill="var(--muted)">小さなシステムなら、単一の文脈で開発できる。</text>'
 + '<text x="540" y="196" font-size="8.5" fill="var(--muted)">物理的には単一の境界、論理的には複数の境界</text>'
 + '<line x1="20" y1="216" x2="760" y2="216" stroke="var(--rule)"/>'
 + '<text x="20" y="238" font-size="9" fill="var(--muted)">③ の場合、複数の業務領域の境界は'
 '<tspan fill="currentColor">名前空間 ・ モジュール ・ パッケージ</tspan>として現れる ── '
 '<tspan fill="var(--key)">実装の側の話になる</tspan></text>'
 + '<text x="20" y="262" font-size="9" fill="var(--key)" font-weight="700">'
 'だから、業務領域は文脈の入れ子にできない</text>'
 + '<text x="20" y="280" font-size="9" fill="var(--muted)">'
 '②も③も起こるので、どちらを外側にしても、もう一方が入らない場合が出る</text>'
 '<rect x="440" y="228" width="320" height="56" rx="3" fill="none" stroke="var(--add)" stroke-width="1.5"/>'
 '<text x="452" y="248" font-size="9.5" font-weight="700" fill="var(--add)">Waffle 自身は ③ である</text>'
 '<text x="452" y="266" font-size="8.5" fill="var(--muted)">業務領域 7本 に対して、区切られた文脈は 1本</text>'
 '<text x="452" y="280" font-size="8.5" fill="var(--muted)">（過去の検討 tier2-domain.html が数えたもの）</text>'
 '</svg>',
 '<b>業務領域は事業方針で決まる構造、区切られた文脈は設計判断である。</b>'
 '対応は1対1に限らず、<b>1つの領域に複数の文脈</b>（課題ごとに別のモデル）も、'
 '<b>1つの文脈に複数の領域</b>（小さなシステムを単一の文脈で開発）も起こる ── '
 'だから<b>どちらを外側にしても入らない場合が出る</b>。'
 '③のとき、領域の境界は名前空間やモジュールとして<b>実装の側に現れる</b>。'
 '<b>そして Waffle 自身が ③ である</b> ── 業務領域7本に対して、区切られた文脈は1本。'
 'だから「入れ子にできない」は机上の話ではなく、<b>いま自分がそうなっている</b>。')

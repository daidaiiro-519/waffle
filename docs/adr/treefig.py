def _t(x, y, lines, tone="var(--muted)", size=9):
    return "".join(f'<text x="{x}" y="{y+i*15}" font-size="{size}" fill="{tone}">{l}</text>'
                   for i, l in enumerate(lines))

TREE = ('<svg viewBox="0 0 780 400" role="img" aria-label="業務でフォルダを切り、その中で接点と基盤の層を分ける置き方と、層でフォルダを切る置き方の比較">'
 '<text x="20" y="22" font-size="10.5" font-weight="700" fill="var(--key)">B　業務でフォルダを切り、その中に層を置く</text>'
 '<rect x="20" y="32" width="380" height="300" fill="none" stroke="var(--key)" stroke-width="1.5"/>'
 + _t(34, 52, [
   "specs/",
   "  予約/　　　　　　　　　　　← 文脈1つ（業務の層）",
   "    context.json　　　　　　境界と、その中の言葉",
   "    model.予約.json　　　　 一貫性の境界ごと",
   "    operation.確定する.json　呼べる操作ごと",
   "    operation.取り消す.json",
   "",
   "    interface.cli/　　　　　← 業務 × 接点",
   "      offer.確定する.json　 名前 ・ 引数 ・ 返り",
   "    interface.mcp/",
   "      offer.確定する.json",
   "    interface.ui/",
   "      offer.予約画面.json",
   "      flow.申し込み.json　　 つながりの順序",
   "",
   "    platform.保存/　　　　　← 業務 × 基盤",
   "      requirement.json　　 指標と目標",
 ], "currentColor")
 + _t(34, 308, ["  integration.予約-請求.json　← 文脈をまたぐ",
                "  area.json　　　　　　　　　 領域（中核 ・ 一般 ・ 補完）"], "var(--add)")
 + '<text x="420" y="22" font-size="10.5" font-weight="700" fill="var(--muted)">A　層でフォルダを切る（Coding と同じ形）</text>'
 '<rect x="420" y="32" width="340" height="290" fill="none" stroke="var(--soft)" stroke-width="1.3"/>'
 + _t(434, 52, [
   "specs/",
   "  domain.予約/",
   "    context.json ・ model.*.json",
   "    operation.*.json",
   "  domain.予約+interface.cli/",
   "    offer.確定する.json",
   "  domain.予約+interface.mcp/",
   "    offer.確定する.json",
   "  domain.予約+interface.ui/",
   "    offer.*.json ・ flow.*.json",
   "  domain.予約+platform.保存/",
   "    requirement.json",
   "  domain.請求/",
   "    …",
 ], "var(--muted)")
 + _t(434, 262, ["同じ業務の文書が、フォルダをまたいで散る",
                 "── 「この業務の全部」を見るのに、",
                 "　　フォルダを横断することになる"], "var(--del)")
 + '<line x1="20" y1="344" x2="760" y2="336" stroke="var(--rule)"/>'
 + _t(20, 362, ["どちらも層は同じ ── 変わるのは、フォルダの切り方だけである。",
                "B は業務が1か所に集まり、A は層が1か所に集まる。"], "var(--muted)")
 + '<text x="20" y="396" font-size="9" fill="var(--key)">業務は主題である（論点15）── '
 '<tspan font-weight="700">主題でまとめるほうが、構造がその決まりを写す</tspan></text>'
 '</svg>',
 '<b>業務 × 接点の文書は、実際に作る。</b>数は「その文脈を、その接点で差し出す能力の数」だけである。'
 '置き方は2つあり、<b>層でフォルダを切ると同じ業務の文書が散り、業務でフォルダを切ると層が散る</b> ── '
 '業務が主題である以上、<b>主題でまとめるほうが決まりを写す。</b>')

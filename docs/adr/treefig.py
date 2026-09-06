def _tree(x0, y0, rows, step=15, indent=16):
    """(深さ, 名前, 注記, 色) の並びを、深さを座標にして描く。

    SVG は行頭の空白を落とすので、字下げは x の値で表す。
    深さが変わる箇所には、親から下ろす縦の線を引く。
    """
    out, ys = [], []
    for i, (d, name, note, tone) in enumerate(rows):
        y = y0 + i * step
        ys.append((d, y))
        x = x0 + d * indent
        if d > 0:
            out.append(f'<line x1="{x - 9}" y1="{y - 4}" x2="{x - 3}" y2="{y - 4}" '
                       f'stroke="var(--soft)" stroke-width="1"/>')
        out.append(f'<text x="{x}" y="{y}" font-size="9" fill="{tone}">{name}</text>')
        if note:
            out.append(f'<text x="{x0 + 208}" y="{y}" font-size="8.5" fill="var(--muted)">{note}</text>')
    # 深さごとに、縦のたて線を引く
    for d in range(0, 4):
        seg = [y for dd, y in ys if dd > d]
        if seg:
            out.append(f'<line x1="{x0 + d * indent - 9}" y1="{y0 - 6}" '
                       f'x2="{x0 + d * indent - 9}" y2="{max(seg) - 4}" '
                       f'stroke="var(--soft)" stroke-width="1"/>')
    return "".join(out)

C, K, A, M = "currentColor", "var(--key)", "var(--add)", "var(--muted)"

TREE = ('<svg viewBox="0 0 780 400" role="img" aria-label="業務でフォルダを切り、その中に接点と基盤の層を置く形と、層でフォルダを切る形の比較">'
 '<text x="20" y="22" font-size="10.5" font-weight="700" fill="var(--key)">B　業務でフォルダを切り、その中に層を置く</text>'
 '<rect x="20" y="32" width="404" height="300" fill="none" stroke="var(--key)" stroke-width="1.5"/>'
 + _tree(36, 52, [
   (0, "specs/", "", M),
   (1, "予約/", "文脈1つ（業務の層）", K),
   (2, "context.json", "境界と、その中の言葉", C),
   (2, "model.予約.json", "一貫性の境界ごと", C),
   (2, "operation.確定する.json", "呼べる操作ごと", C),
   (2, "operation.取り消す.json", "", C),
   (2, "interface.cli/", "業務 × 接点", A),
   (3, "offer.確定する.json", "名前 ・ 引数 ・ 返り", C),
   (2, "interface.mcp/", "", A),
   (3, "offer.確定する.json", "", C),
   (2, "interface.ui/", "", A),
   (3, "offer.予約画面.json", "", C),
   (3, "flow.申し込み.json", "つながりの順序", C),
   (2, "platform.保存/", "業務 × 基盤", A),
   (3, "requirement.json", "指標と目標", C),
   (1, "integration.予約-請求.json", "文脈をまたぐ", A),
   (1, "area.json", "領域（中核 ・ 一般 ・ 補完）", A),
 ])
 + '<text x="440" y="22" font-size="10.5" font-weight="700" fill="var(--muted)">A　層でフォルダを切る（Coding と同じ形）</text>'
 '<rect x="440" y="32" width="320" height="300" fill="none" stroke="var(--soft)" stroke-width="1.3"/>'
 + _tree(454, 52, [
   (0, "specs/", "", M),
   (1, "domain.予約/", "", M),
   (2, "context.json", "", M),
   (2, "operation.確定する.json", "", M),
   (1, "domain.予約+interface.cli/", "", M),
   (2, "offer.確定する.json", "", M),
   (1, "domain.予約+interface.mcp/", "", M),
   (2, "offer.確定する.json", "", M),
   (1, "domain.予約+interface.ui/", "", M),
   (2, "offer.予約画面.json", "", M),
   (2, "flow.申し込み.json", "", M),
   (1, "domain.予約+platform.保存/", "", M),
   (2, "requirement.json", "", M),
   (1, "domain.請求/", "", M),
   (2, "…", "", M),
 ])
 + '<text x="452" y="300" font-size="8.5" fill="var(--del)">同じ業務の文書が、フォルダをまたいで散る</text>'
 '<text x="452" y="316" font-size="8.5" fill="var(--del)">「この業務の全部」を見るのに、横断することになる</text>'
 '<line x1="20" y1="346" x2="760" y2="346" stroke="var(--rule)"/>'
 '<text x="20" y="366" font-size="9" fill="var(--muted)">どちらも層は同じ ── 変わるのは、フォルダの切り方だけである。'
 'B は業務が1か所に集まり、A は層が1か所に集まる</text>'
 '<text x="20" y="388" font-size="9" fill="var(--key)">業務は主題である（論点15）── '
 '<tspan font-weight="700">主題でまとめるほうが、構造がその決まりを写す</tspan></text>'
 '</svg>',
 '<b>業務 × 接点の文書は、実際に作る。</b>数は「その文脈を、その接点で差し出す能力の数」だけである。'
 '置き方は2つあり、<b>層でフォルダを切ると同じ業務の文書が散り、業務でフォルダを切ると層が散る</b> ── '
 '業務が主題である以上、<b>主題でまとめるほうが決まりを写す。</b>')

def _cell(x, y, w, h, txt, stroke="var(--soft)", fill="none", tone="var(--muted)", bold=False, sw="1"):
    fw = ' font-weight="700"' if bold else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            f'<text x="{x+w/2}" y="{y+h/2+4}" text-anchor="middle" font-size="10" fill="{tone}"{fw}>{txt}</text>')

TYPES = ["表", "文", "図＋読み方", "並び"]
OUTS = ["Markdown", "HTML", "射影なし"]
DEF = [["罫線の表", "罫線の表", "─"], ["段落", "段落", "─"], ["画像＋一文", "画像＋一文", "─"], ["箇条書き", "箇条書き", "─"]]
OVER = {(0, 1): "札の並び", (2, 1): "図と説明"}

rows = ""
for i, t in enumerate(TYPES):
    rows += f'<text x="20" y="{78+i*30+14}" font-size="10.5" fill="currentColor">{t}</text>'
    for j in range(3):
        rows += _cell(78+j*76, 78+i*30, 74, 26, DEF[i][j])
heads = "".join(f'<text x="{78+j*76+37}" y="70" text-anchor="middle" font-size="10" fill="var(--muted)">{o}</text>'
                for j, o in enumerate(OUTS))
over = ""
for i, t in enumerate(TYPES):
    over += f'<text x="330" y="{78+i*30+14}" font-size="10.5" fill="currentColor">{t}</text>'
    for j in range(3):
        v = OVER.get((i, j))
        if v:
            over += _cell(388+j*76, 78+i*30, 74, 26, v, "var(--add)", "rgba(154,91,44,.10)", "var(--add)", True, "1.8")
        elif i == 3 and j == 0:
            over += _cell(388+j*76, 78+i*30, 74, 26, "欠け", "var(--del)", "none", "var(--del)", True, "1.6")
        else:
            over += _cell(388+j*76, 78+i*30, 74, 26, "", "var(--rule)")
overheads = "".join(f'<text x="{388+j*76+37}" y="70" text-anchor="middle" font-size="10" fill="var(--muted)">{o}</text>'
                    for j, o in enumerate(OUTS))

PROJTBL = ('<svg viewBox="0 0 780 250" role="img" aria-label="abstract が既定の射影を全部持ち、実際に書くのは既定から外れた差分だけである。既定も差分も無い欄は描画時に落ちる">'
 '<text x="20" y="30" font-size="12" font-weight="700" fill="var(--muted)">abstract が持つ既定　── 全部埋まっている</text>'
 '<text x="20" y="48" font-size="10.5" fill="var(--muted)">型を足したら、ここに1行足す（既定だけ）</text>'
 + heads + rows +
 '<line x1="310" y1="20" x2="310" y2="238" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="330" y="30" font-size="12" font-weight="700" fill="var(--add)">人が書くのは、ここだけ　── 既定と違うマスの上書き</text>'
 '<text x="330" y="48" font-size="10.5" fill="var(--muted)">1マスに書くのは「その型を、その出力先でどう出すか」1つ</text>'
 + overheads + over +
 '<text x="330" y="228" font-size="10.5" fill="var(--del)">■ 既定も差分も無い欄は、描画時に落ちる（穴が見える）</text>'
 '</svg>',
 '<b>射影の表は「型 × 出力先」だが、人が触るのはそのうち数マスである。</b>'
 '既定を abstract が持てば、型を足しても増えるのは既定の1行だけで、'
 '<b>書く量は掛け算で増えない</b>。既定も差分も無いマスは描かずに落とし、欄が無いことを見えるようにする。')

GROUPPROJ = ('<svg viewBox="0 0 780 260" role="img" aria-label="組の射影が並べ方だけを持ち、中の部品の出し方は部品の射影に委ねる形と、組が全部書く形の比較">'
 '<defs><marker id="gp1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--key)"/></marker>'
 '<marker id="gp2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--del)"/></marker></defs>'
 '<text x="20" y="24" font-size="12" font-weight="700" fill="var(--del)">組が、中身の出し方まで書く</text>'
 '<rect x="20" y="40" width="320" height="46" fill="none" stroke="var(--del)" stroke-width="1.6"/>'
 '<text x="180" y="60" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--del)">組「案の比較 ＋ 結論」の射影</text>'
 '<text x="180" y="78" text-anchor="middle" font-size="10" fill="var(--muted)">並べ方 ＋ 表の出し方 ＋ 文の出し方</text>'
 '<rect x="20" y="104" width="100" height="30" fill="none" stroke="var(--rule)"/>'
 '<text x="70" y="123" text-anchor="middle" font-size="10" fill="var(--muted)">Markdown</text>'
 '<rect x="130" y="104" width="100" height="30" fill="none" stroke="var(--rule)"/>'
 '<text x="180" y="123" text-anchor="middle" font-size="10" fill="var(--muted)">HTML</text>'
 '<rect x="240" y="104" width="100" height="30" fill="none" stroke="var(--rule)"/>'
 '<text x="290" y="123" text-anchor="middle" font-size="10" fill="var(--muted)">射影なし</text>'
 '<line x1="180" y1="86" x2="180" y2="100" stroke="var(--del)" stroke-width="1.4" marker-end="url(#gp2)"/>'
 '<text x="20" y="164" font-size="11" fill="var(--del)">組 × 出力先 × 中の部品ぶん、欄が要る。</text>'
 '<text x="20" y="182" font-size="11" fill="var(--del)">同じ「表の出し方」が、組の数だけ写される</text>'
 '<text x="20" y="208" font-size="11" fill="var(--muted)">表の出し方を直すとき、</text>'
 '<text x="20" y="226" font-size="11" fill="var(--muted)">組の数だけ直して回ることになる</text>'
 '<line x1="380" y1="14" x2="380" y2="248" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="410" y="24" font-size="12" font-weight="700" fill="var(--key)">組は、並べ方だけを書く</text>'
 '<rect x="410" y="40" width="340" height="46" fill="none" stroke="var(--key)" stroke-width="1.8"/>'
 '<text x="580" y="60" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--key)">組「案の比較 ＋ 結論」の射影</text>'
 '<text x="580" y="78" text-anchor="middle" font-size="10" fill="var(--muted)">並べ方だけ ── 「結論を先に、表を後に」</text>'
 '<rect x="410" y="120" width="160" height="44" fill="none" stroke="var(--key)" stroke-width="1.4"/>'
 '<text x="490" y="139" text-anchor="middle" font-size="10.5" fill="var(--key)">部品「表」の射影</text>'
 '<text x="490" y="155" text-anchor="middle" font-size="9.5" fill="var(--muted)">罫線の表 ／ 札の並び</text>'
 '<rect x="590" y="120" width="160" height="44" fill="none" stroke="var(--key)" stroke-width="1.4"/>'
 '<text x="670" y="139" text-anchor="middle" font-size="10.5" fill="var(--key)">部品「文」の射影</text>'
 '<text x="670" y="155" text-anchor="middle" font-size="9.5" fill="var(--muted)">段落 ／ 見出し付きの札</text>'
 '<line x1="490" y1="86" x2="490" y2="116" stroke="var(--key)" stroke-width="1.4" marker-end="url(#gp1)"/>'
 '<line x1="670" y1="86" x2="670" y2="116" stroke="var(--key)" stroke-width="1.4" marker-end="url(#gp1)"/>'
 '<text x="520" y="104" font-size="10" fill="var(--key)">出し方は、こちらに任せる</text>'
 '<text x="410" y="192" font-size="11" fill="var(--key)">組が持つ欄は、出力先ごとに1つ（並べ方）。</text>'
 '<text x="410" y="210" font-size="11" fill="var(--muted)">組が増えても、部品の射影は増えない</text>'
 '<text x="410" y="236" font-size="11" fill="var(--muted)">表の出し方を直せば、全ての組に効く</text>'
 '</svg>',
 '<b>組は「何を先に、何を後に置くか」だけを書く。</b>中の表をどう出すかは部品の射影が持つ。'
 'こうすると組の欄は<b>組 × 出力先</b>で済み、しかも表の出し方を直したときに、それを使う全ての組へ一度に効く。')

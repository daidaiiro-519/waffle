def _row(x, y, w, h, cells, widths, head=False, tone="var(--muted)"):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"var(--chip,rgba(128,128,128,.10))" if head else "none"}" stroke="var(--soft)" stroke-width="1"/>'
    cx = x
    for i, (c, cw) in enumerate(zip(cells, widths)):
        if i:
            out += f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{y+h}" stroke="var(--soft)" stroke-width="1"/>'
        out += (f'<text x="{cx+8}" y="{y+h/2+4}" font-size="9.5" fill="{tone}"'
                f'{" font-weight=\"700\"" if head else ""}>{c}</text>')
        cx += cw
    return out

DIFF = ('<svg viewBox="0 0 780 400" role="img" aria-label="同じ1つの節が、差分を書かないと罫線の表として、差分を当てると札の並びとして描かれる。節も型も変わらない">'
 '<defs><marker id="df1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--muted)"/></marker>'
 '<marker id="df2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--add)"/></marker></defs>'
 '<text x="20" y="24" font-size="11.5" font-weight="700" fill="var(--muted)">同じ1つの節（document.json）</text>'
 '<rect x="20" y="36" width="330" height="86" fill="none" stroke="currentColor" stroke-width="1.5"/>'
 '<text x="36" y="58" font-size="10.5" fill="currentColor">型　＝　表</text>'
 '<text x="36" y="78" font-size="10.5" fill="var(--muted)">列　＝　案　／　代償</text>'
 '<text x="36" y="98" font-size="10.5" fill="var(--muted)">行　＝　A … ／ B … ／ C …</text>'
 '<text x="368" y="66" font-size="11" fill="var(--muted)">節も型も、</text>'
 '<text x="368" y="84" font-size="11" fill="var(--muted)">どちらの場合も同じものである</text>'
 '<text x="368" y="108" font-size="11" fill="var(--add)">変わるのは、出力だけ</text>'
 '<line x1="20" y1="140" x2="760" y2="140" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="20" y="164" font-size="11.5" font-weight="700" fill="var(--muted)">差分を書かない　── 既定のまま</text>'
 '<rect x="20" y="176" width="330" height="26" fill="none" stroke="var(--rule)" stroke-width="1" stroke-dasharray="4 3"/>'
 '<text x="185" y="193" text-anchor="middle" font-size="10" fill="var(--muted)">射影の表の「表 × HTML」は空　── 既定が使われる</text>'
 '<line x1="185" y1="202" x2="185" y2="222" stroke="var(--muted)" stroke-width="1.3" marker-end="url(#df1)"/>'
 '<text x="20" y="240" font-size="10" fill="var(--muted)">HTML の出力</text>'
 + _row(20, 246, 330, 24, ["案", "代償"], [140, 190], head=True, tone="currentColor")
 + _row(20, 270, 330, 24, ["A　型＝形", "出したい形の数だけ型が要る"], [140, 190])
 + _row(20, 294, 330, 24, ["B　型 × 射影", "射影の対応表が要る"], [140, 190])
 + _row(20, 318, 330, 24, ["C　文書ごとの雛形", "形から意味を読めない"], [140, 190])
 + '<text x="20" y="362" font-size="10.5" fill="var(--muted)">罫線の表。Markdown と同じ形で出る</text>'
 '<line x1="390" y1="150" x2="390" y2="380" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="430" y="164" font-size="11.5" font-weight="700" fill="var(--add)">差分を1マスだけ書く</text>'
 '<rect x="430" y="176" width="330" height="26" fill="none" stroke="var(--add)" stroke-width="1.6"/>'
 '<text x="595" y="193" text-anchor="middle" font-size="10" font-weight="700" fill="var(--add)">表 × HTML　＝　札の並び</text>'
 '<line x1="595" y1="202" x2="595" y2="222" stroke="var(--add)" stroke-width="1.4" marker-end="url(#df2)"/>'
 '<text x="430" y="240" font-size="10" fill="var(--muted)">HTML の出力</text>'
 '<rect x="430" y="246" width="330" height="30" fill="none" stroke="var(--add)" stroke-width="1.4" rx="3"/>'
 '<text x="442" y="260" font-size="10" font-weight="700" fill="var(--add)">A　型＝形</text>'
 '<text x="442" y="272" font-size="9" fill="var(--muted)">出したい形の数だけ型が要る</text>'
 '<rect x="430" y="282" width="330" height="30" fill="none" stroke="var(--add)" stroke-width="1.4" rx="3"/>'
 '<text x="442" y="296" font-size="10" font-weight="700" fill="var(--add)">B　型 × 射影</text>'
 '<text x="442" y="308" font-size="9" fill="var(--muted)">射影の対応表が要る</text>'
 '<rect x="430" y="318" width="330" height="30" fill="none" stroke="var(--add)" stroke-width="1.4" rx="3"/>'
 '<text x="442" y="332" font-size="10" font-weight="700" fill="var(--add)">C　文書ごとの雛形</text>'
 '<text x="442" y="344" font-size="9" fill="var(--muted)">形から意味を読めない</text>'
 '<text x="430" y="362" font-size="10.5" fill="var(--add)">札の並び。<tspan fill="var(--muted)">Markdown は罫線の表のまま（そのマスは触っていない）</tspan></text>'
 '</svg>',
 '<b>差分を当てても、節も型も1文字も変わらない。</b>射影の表の1マス「表 × HTML」に「札の並び」と書いただけで、'
 'HTML の出力が罫線の表から札の並びへ変わる。<b>Markdown のマスは触っていないので、そちらは罫線の表のまま出る。</b>'
 'AI が読む構造も変わらない ── 射影を通さないからである。')

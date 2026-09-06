def _band(y, h, name, axes, kinds, cannot, tone="var(--key)"):
    return (f'<rect x="130" y="{y}" width="420" height="{h}" fill="none" stroke="{tone}" stroke-width="1.5"/>'
            f'<text x="20" y="{y+20}" font-size="10.5" font-weight="700" fill="{tone}">{name}</text>'
            f'<text x="20" y="{y+36}" font-size="8.5" fill="var(--muted)">軸： {axes}</text>'
            + "".join(f'<text x="144" y="{y+20+i*16}" font-size="9" fill="currentColor">{k}</text>'
                      for i, k in enumerate(kinds))
            + f'<text x="566" y="{y+20}" font-size="8.5" fill="var(--muted)">決められない：</text>'
            + "".join(f'<text x="566" y="{y+34+i*14}" font-size="8.5" fill="var(--muted)">{c}</text>'
                      for i, c in enumerate(cannot)))

CODLAYER = ('<svg viewBox="0 0 780 420" role="img" aria-label="CodingSchema の層構造。軸の組み合わせが層になり、層ごとに置く種が違う">'
 '<defs><marker id="cl1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--add)"/></marker></defs>'
 '<text x="20" y="22" font-size="10" font-weight="700" fill="var(--muted)">層</text>'
 '<text x="144" y="22" font-size="9" fill="var(--muted)">その層に置く種（＝雛形1つ）</text>'
 '<text x="566" y="22" font-size="9" fill="var(--muted)">その層では決まらないこと</text>'
 + _band(32, 96, "言語", "言語",
         ["style　　　　綴りと書式", "failure　　　失敗の運び方", "concurrency　並行と共有",
          "test-mechanism　テストの仕組み", "toolchain　　標準の道具"],
         ["どんな層があるか", "（アーキテクチャが決める）", "何を保証するか", "（用途が決める）"])
 + _band(140, 64, "アーキテクチャ", "アーキテクチャ",
         ["layers　　　　構成要素と責務", "dependency　　依存の向き", "test-boundaries　確かめる単位"],
         ["それを何で表すか", "（言語が決める）"])
 + _band(216, 50, "言語 × アーキテクチャ", "言語 ・ アーキテクチャ",
         ["layer-mapping　言語での表し方", "test-placement　テストの置き場所"],
         ["何を保証するか", "（用途が決める）"])
 + _band(278, 96, "用途", "用途（＋ 実行環境）",
         ["contract　　　外部との契約", "lifecycle　　　起動と終了", "acceptance　　保証する振る舞い",
          "test-strategy　テストの重心", "stack　　　　採用する依存"],
         ["── ここが可変で、", "上の3層が空けた穴を埋める"], "var(--add)")
 + '<path d="M120 326 C 66 326, 66 168, 118 168" fill="none" stroke="var(--add)" stroke-width="1.5" marker-end="url(#cl1)"/>'
 '<text x="14" y="196" font-size="8.5" fill="var(--add)">用途が、採る</text>'
 '<text x="14" y="208" font-size="8.5" fill="var(--add)">アーキを指定</text>'
 '<line x1="20" y1="392" x2="760" y2="392" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="20" y="384" font-size="9" fill="var(--muted)">実体の例：<tspan fill="currentColor">CodingSchema（種＝failure、軸＝言語:rust）</tspan>'
 '　→　<tspan fill="var(--key)">Rust における失敗の運び方</tspan></text>'
 '<text x="20" y="410" font-size="9" fill="var(--muted)">層は宣言された軸から導出されるので、'
 '<tspan fill="var(--key)" font-weight="700">層をあらかじめ並べない</tspan>。軸の組み合わせが現れた数だけ在る</text>'
 '</svg>',
 '<b>層は軸の組み合わせで、種は雛形の単位である。</b>'
 '上の3層はそれぞれ「その層でしか決まらないこと」だけを持ち、決められないことは下へ穴として空ける ── '
 '<b>用途の層が、その穴を埋める。</b>そして用途は、採用するアーキテクチャを指定して上の層を選ぶ。')

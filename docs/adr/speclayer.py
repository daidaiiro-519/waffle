def _b(y, h, name, axes, kinds, tone="var(--key)"):
    return (f'<rect x="150" y="{y}" width="430" height="{h}" fill="none" stroke="{tone}" stroke-width="1.5"/>'
            f'<text x="20" y="{y+20}" font-size="10.5" font-weight="700" fill="{tone}">{name}</text>'
            f'<text x="20" y="{y+35}" font-size="8.5" fill="var(--muted)">軸： {axes}</text>'
            + "".join(f'<text x="164" y="{y+20+i*15}" font-size="9" fill="currentColor">{k}</text>'
                      for i, k in enumerate(kinds)))

SPECLAYER = ('<svg viewBox="0 0 780 360" role="img" aria-label="spec も軸を宣言し、層を導出して種を置く。Coding と同じ形になる">'
 '<text x="20" y="22" font-size="11" font-weight="700" fill="var(--muted)">spec の軸　── 何が正しいかは、何に依存して変わるか</text>'
 '<rect x="20" y="32" width="170" height="60" fill="none" stroke="currentColor" stroke-width="1.4"/>'
 '<text x="105" y="52" text-anchor="middle" font-size="10" fill="currentColor">業務</text>'
 '<text x="105" y="70" text-anchor="middle" font-size="8.5" fill="var(--muted)">何を成すか</text>'
 '<text x="105" y="84" text-anchor="middle" font-size="8" fill="var(--muted)">（接点も基盤も知らない）</text>'
 '<rect x="205" y="32" width="170" height="60" fill="none" stroke="currentColor" stroke-width="1.4"/>'
 '<text x="290" y="52" text-anchor="middle" font-size="10" fill="currentColor">接点</text>'
 '<text x="290" y="70" text-anchor="middle" font-size="8.5" fill="var(--muted)">誰に差し出すか</text>'
 '<text x="290" y="84" text-anchor="middle" font-size="8" fill="var(--muted)">人 ／ 別のシステム ／ AI</text>'
 '<rect x="390" y="32" width="170" height="60" fill="none" stroke="currentColor" stroke-width="1.4"/>'
 '<text x="475" y="52" text-anchor="middle" font-size="10" fill="currentColor">基盤</text>'
 '<text x="475" y="70" text-anchor="middle" font-size="8.5" fill="var(--muted)">どこで動かすか</text>'
 '<text x="475" y="84" text-anchor="middle" font-size="8" fill="var(--muted)">（業務も接点も知らない）</text>'
 '<text x="580" y="56" font-size="8.5" fill="var(--muted)">1つを固定しても、</text>'
 '<text x="580" y="70" font-size="8.5" fill="var(--muted)">他が動く ── だから軸である</text>'
 '<line x1="20" y1="108" x2="760" y2="108" stroke="var(--rule)" stroke-width="1"/>'
 '<text x="20" y="128" font-size="10" font-weight="700" fill="var(--muted)">層（導出）</text>'
 '<text x="164" y="128" font-size="9" fill="var(--muted)">その層で決まることの単位（＝種）</text>'
 + _b(140, 52, "業務", "業務",
      ["業務の構造（何が在るか）", "業務の振る舞い（何が起きるか）"])
 + _b(202, 38, "接点", "接点",
      ["約束（誰が呼び、何を渡し、何が返り、失敗はどうなるか）"])
 + _b(250, 38, "基盤", "基盤",
      ["満たすべき要件（容量 ・ 耐障害 ・ 保全）"])
 + _b(298, 38, "業務 × 接点", "業務 ・ 接点",
      ["その業務を、その接点でどう差し出すか"], "var(--add)")
 + '<text x="596" y="164" font-size="8.5" fill="var(--muted)">上の層は、下の層を知らない</text>'
 '<text x="596" y="222" font-size="8.5" fill="var(--muted)">層をまたぐことは、掛けた層で書く</text>'
 '<text x="596" y="318" font-size="8.5" fill="var(--add)">画面か API かは、ここで分かれる</text>'
 '<text x="20" y="348" font-size="9" fill="var(--muted)">Coding と同じ形になる ──'
 '<tspan fill="var(--key)" font-weight="700">軸を宣言し、層は導出し、種はその層で決まることの単位</tspan>（論点16）</text>'
 '</svg>',
 '<b>spec も、軸を宣言して層を導出する形にできる。</b>'
 '業務・接点・基盤は互いに独立に動くので軸として立ち、掛け合わせは掛けた層で書く ── '
 '<b>「画面向けの spec」「API 向けの spec」を別の型にするのではなく、接点という軸の値として扱う。</b>')

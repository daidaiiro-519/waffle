def _row(y, name, unit, why, tone="currentColor"):
    return (f'<text x="34" y="{y}" font-size="9.5" fill="{tone}">{name}</text>'
            f'<text x="190" y="{y}" font-size="9" fill="var(--muted)">{unit}</text>'
            f'<text x="430" y="{y}" font-size="8.5" fill="var(--muted)">{why}</text>')

SPECKINDS = ('<svg viewBox="0 0 780 400" role="img" aria-label="層ごとに、その層でしか決まらないことを単位へ切る">'
 '<text x="34" y="22" font-size="9" fill="var(--muted)">その層で決まること</text>'
 '<text x="190" y="22" font-size="9" fill="var(--muted)">1つの文書として閉じる単位</text>'
 '<text x="430" y="22" font-size="9" fill="var(--muted)">なぜ、そこで切れるか</text>'
 '<line x1="20" y1="30" x2="760" y2="30" stroke="var(--rule)"/>'
 '<text x="20" y="52" font-size="10.5" font-weight="700" fill="var(--key)">業務の層</text>'
 '<rect x="20" y="60" width="740" height="132" fill="none" stroke="var(--key)" stroke-width="1.5"/>'
 + _row(80, "事業の区切り", "領域　── 中核 ・ 一般 ・ 補完", "どこに力を入れるかは、領域ごとに1度決まる")
 + _row(102, "言葉の通じる範囲", "文脈　── 境界と、その中の言葉", "同じ言葉が一貫する範囲そのものが単位である")
 + _row(124, "業務の構造", "モデル　── 実体 ・ 値 ・ 一貫性の境界", "一貫性の境界より小さくは切れない")
 + _row(146, "業務の振る舞い", "操作　── 事前 ・ 事後 ・ 受け入れ基準", "呼べる操作1つが、約束1つになる")
 + _row(168, "文脈どうしの連係", "連係　── 上流 ・ 下流 ・ 変換の要否", "2つの文脈の間にしか無いので、どちらにも属さない")
 + '<text x="20" y="214" font-size="10.5" font-weight="700" fill="var(--add)">業務 × 接点の層</text>'
 '<rect x="20" y="222" width="740" height="66" fill="none" stroke="var(--add)" stroke-width="1.5"/>'
 + _row(242, "差し出しの約束", "この能力を、この接点でどう呼べるか", "能力 × 接点 の組ごとに1つ", "var(--add)")
 + _row(264, "つながりの順序", "複数の差し出しを、どの順で通るか", "画面の遷移や、対話の流れがこれに当たる", "var(--add)")
 + '<text x="20" y="310" font-size="10.5" font-weight="700" fill="var(--add)">業務 × 基盤の層</text>'
 '<rect x="20" y="318" width="740" height="44" fill="none" stroke="var(--add)" stroke-width="1.5"/>'
 + _row(340, "満たすべき要件", "この業務に、どの水準が要るか", "指標と目標の組で書ける（SLI ・ SLO）", "var(--add)")
 + '<line x1="20" y1="374" x2="760" y2="374" stroke="var(--rule)"/>'
 '<text x="20" y="392" font-size="9" fill="var(--muted)">切る単位は「1つの文書として閉じるか」で決める ──'
 '<tspan fill="var(--key)" font-weight="700">閉じない単位は、種にしても中身が他へこぼれる</tspan></text>'
 '</svg>',
 '<b>層ごとに、その層でしか決まらないことを単位へ切った。</b>'
 '業務は5つ（領域 ・ 文脈 ・ モデル ・ 操作 ・ 連係）、業務 × 接点は2つ（差し出しの約束 ・ つながりの順序）、'
 '業務 × 基盤は1つ（満たすべき要件）── <b>合わせて8つが、いまの見立てである。</b>')

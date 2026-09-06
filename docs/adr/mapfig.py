def _b(x, y, w, h, label, stroke, sw=1.3, size=9, sub=None, bold=True):
    fw = ' font-weight="700"' if bold else ""
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" stroke="{stroke}" stroke-width="{sw}"/>'
           f'<text x="{x + w/2}" y="{y + (20 if sub else h/2 + 3.5)}" text-anchor="middle" font-size="{size}" fill="{stroke}"{fw}>{label}</text>')
    if sub:
        out += (f'<text x="{x + w/2}" y="{y + 36}" text-anchor="middle" font-size="8" '
                f'fill="var(--muted)">{sub}</text>')
    return out

def _t(x, y, s, tone="var(--muted)", size=8.5, anchor=None, bold=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    fw = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"

MAP = ('<svg viewBox="0 0 780 260" role="img" aria-label="線は参照から導き、方法は宣言から取り、地図は描いて、読み取りは検査で出す">'
 '<defs><marker id="mp1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
 '<path d="M0 0 L10 5 L0 10 z" fill="var(--key)"/></marker></defs>'
 + _t(20, 20, "文脈の地図を、どう描くか", M, 10, bold=True)
 + _b(20, 32, 180, 52, "線　── 導き出す", C, 1.3, 9, "文書どうしの参照から、頂点と辺が出る")
 + _b(20, 96, 180, 52, "方法　── 宣言から取る", A, 1.5, 9, "共用サービス ／ 変換装置 …")
 + _t(20, 168, "参照だけでは、つながっていることしか分からない", M, 8.5)
 + _t(20, 184, "どの方法でつなぐか ・ 上流と下流のどちらに決定権があるかは、", M, 8.5)
 + _t(20, 200, "人が決めることなので、書かないと出てこない", D, 8.5)
 + '<line x1="200" y1="58" x2="248" y2="80" stroke="var(--key)" stroke-width="1.5" marker-end="url(#mp1)"/>'
 + '<line x1="200" y1="122" x2="248" y2="100" stroke="var(--key)" stroke-width="1.5" marker-end="url(#mp1)"/>'
 + _b(254, 62, 170, 56, "地図を描く", K, 1.8, 9.5, "頂点 ＝ 文脈、辺 ＝ 方法")
 + '<line x1="424" y1="90" x2="472" y2="90" stroke="var(--key)" stroke-width="1.5" marker-end="url(#mp1)"/>'
 + _b(478, 32, 282, 52, "読み取りの材料を出す", K, 1.5, 9, "同じ相手へ変換装置が集まる ／ 孤立した文脈")
 + _b(478, 96, 282, 52, "ずれを検める", K, 1.5, 9, "宣言では別々の道なのに、参照が在る")
 + _t(478, 172, "どちらも取り決めを数えれば出るので、述語で書ける規則になる", M, 8.5)
 + _t(478, 188, "（論点6 の検査。承認の材料に並ぶ ── 論点7）", M, 8.5)
 + '<line x1="20" y1="216" x2="760" y2="216" stroke="var(--rule)"/>'
 + _t(20, 236, "描く動詞は abstract が持ち、「地図」という具体の引き方と検査は concrete（Spec）が宣言する", K, 9, bold=True)
 + _t(20, 252, "合図が何を意味するか（組織の課題）は、人が読む", M, 8.5)
 + '</svg>',
 '<b>線は参照から導き、方法は宣言から取る。</b>'
 '文書どうしの参照を集めれば、どの文脈とどの文脈がつながっているかは出てくる ── '
 'しかし<b>どの方法でつなぐか、上流と下流のどちらに決定権があるかは、人が決めることなので書かないと出てこない</b>。'
 '両方そろうと、地図が描け、読み取りの材料が出せ、<b>宣言と実際の参照のずれも検められる</b>。')

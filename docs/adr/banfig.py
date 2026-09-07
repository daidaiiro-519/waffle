def _b(x, y, w, h, label, stroke, sw=1.3, size=8.5, ly=None, bold=False):
    fw = ' font-weight="700"' if bold else ""
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" stroke="{stroke}" stroke-width="{sw}"/>'
    if label:
        out += (f'<text x="{x + w/2}" y="{y + (ly or h/2 + 3.5)}" text-anchor="middle" '
                f'font-size="{size}" fill="{stroke}"{fw}>{label}</text>')
    return out

def _t(x, y, s, tone="var(--muted)", size=8.5, anchor=None, bold=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    fw = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"
AR = ('<defs><marker id="banA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
      'markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

BAN = ('<svg viewBox="0 0 780 372" role="img" aria-label="禁止は、規則という述語と、接点がその結果をどう扱うかの2つに割れる">'
 + AR
 + _t(20, 20, "「禁止は規則へ」と書いたが、それだと規則が止める力を持つ ── 動詞が増える", D, 10, bold=True)
 + _b(20, 32, 250, 52, "", D, 1.2)
 + _t(145, 52, "規則が、判定して止める", D, 9, "middle", True)
 + _t(145, 68, "abstract の動詞に「止める」が要る", D, 8, "middle")
 + '<line x1="20" y1="100" x2="760" y2="100" stroke="var(--rule)"/>'
 + _t(20, 124, "割ると、どちらも既にある仕組みで足りる", K, 10, bold=True)
 + _b(20, 138, 250, 130, "", K, 1.6)
 + _t(145, 158, "規則 ── 述語", K, 9, "middle", True)
 + _b(38, 170, 214, 40, "", C, 1.1)
 + _t(145, 186, "この書き込みは、", C, 8.5, "middle")
 + _t(145, 200, "禁じた場所を指すか", C, 8.5, "middle")
 + _t(145, 228, "返すのは 真 か 偽 だけ", M, 8, "middle")
 + _t(145, 250, "止める力は持たない", K, 8.5, "middle", True)
 + f'<line x1="270" y1="200" x2="316" y2="200" stroke="var(--key)" stroke-width="1.5" marker-end="url(#banA)"/>'
 + _t(293, 192, "偽のとき", K, 8, "middle")
 + _b(324, 138, 436, 130, "", A, 1.3)
 + _t(542, 158, "接点 ── 同じ判定を、どう扱うか", A, 9, "middle", True)
 + _b(340, 172, 132, 68, "", C, 1.1)
 + _t(406, 190, "Hook", C, 8.5, "middle", True)
 + _t(406, 208, "その場で止める", C, 8.5, "middle")
 + _t(406, 226, "書き込ませない", M, 8, "middle")
 + _b(478, 172, 132, 68, "", C, 1.1)
 + _t(544, 190, "CLI", C, 8.5, "middle", True)
 + _t(544, 208, "終了コードで返す", C, 8.5, "middle")
 + _t(544, 226, "止めはしない", M, 8, "middle")
 + _b(616, 172, 132, 68, "", C, 1.1)
 + _t(682, 190, "承認の材料", C, 8.5, "middle", True)
 + _t(682, 208, "違反として並べる", C, 8.5, "middle")
 + _t(682, 226, "人が見て決める", M, 8, "middle")
 + _t(542, 258, "掛かることは、掛けた層に書く（論点15）", A, 8.5, "middle", True)
 + '<line x1="20" y1="288" x2="760" y2="288" stroke="var(--rule)"/>'
 + _t(20, 310, "規則は1本のまま、扱いが3つある ── 規則を接点の数だけ持つのでも、動詞を増やすのでもない", K, 9, bold=True)
 + _t(20, 332, "止める6本の hook は、規則1本と、Hook という接点の「止める」という扱いに分かれる", M, 9)
 + _t(20, 352, "同じ規則を CLI から呼べば報告になり、承認の列に出せば未検の1行になる", M, 9)
 + '</svg>',
 '<b>「禁止は規則へ」は不正確だった。</b>規則は述語で、真偽しか返さない ── 止める力は持てない（持たせると abstract の動詞が増え、論点5 に反する）。'
 '<b>禁止は、規則（何が違反か）と、接点がその判定をどう扱うか（止める ・ 報告する ・ 並べる）の2つに割れる。</b>'
 '割れば、規則は1本のまま Hook では止まり、CLI では報告になる。')

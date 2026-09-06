def _b(x, y, w, h, label, stroke, sw=1.3, size=9, ly=None, bold=False, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    fw = ' font-weight="700"' if bold else ""
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="none" '
           f'stroke="{stroke}" stroke-width="{sw}"{da}/>')
    if label:
        out += (f'<text x="{x + w/2}" y="{y + (ly or h/2 + 3.5)}" text-anchor="middle" '
                f'font-size="{size}" fill="{stroke}"{fw}>{label}</text>')
    return out

def _t(x, y, s, tone="var(--muted)", size=8.5, anchor=None, bold=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    fw = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'

K, A, M, C, D = "var(--key)", "var(--add)", "var(--muted)", "currentColor", "var(--del)"

SIZE = ('<svg viewBox="0 0 780 300" role="img" aria-label="文脈の上限は言葉の一貫性で決まり、その内側をどこまで割るかは事情で決まる">'
 + _t(20, 20, "上限は、言葉で決まる　── ここは動かせない", K, 10, bold=True)
 + _b(20, 32, 500, 56, "", K, 1.8)
 + _t(270, 54, "同じ言葉が一貫する、もっとも広い範囲", K, 9.5, "middle", True)
 + _t(270, 72, "これ以上広げると、一貫性が失われる", M, 8.5, "middle")
 + _t(536, 56, "超えた瞬間、同じ語が", D, 8.5)
 + _t(536, 72, "2つの意味を持ちはじめる", D, 8.5)
 + _t(20, 118, "内側をどこまで割るかは、事情で決まる　── ここは設計判断", A, 10, bold=True)
 + _b(20, 130, 500, 56, "", M, 1.2, dash="5 4")
 + _b(34, 142, 150, 32, "割らない", M, 1.1, 8.5)
 + _b(196, 142, 150, 32, "2つに割る", M, 1.1, 8.5)
 + _b(358, 142, 148, 32, "3つに割る", M, 1.1, 8.5)
 + _t(536, 152, "どれも上限の内側なら、", M, 8.5)
 + _t(536, 168, "DDD としては正しい", M, 8.5)
 + _t(20, 210, "割る理由は、3つだけ挙がっている", A, 9.5, bold=True)
 + _b(20, 220, 236, 30, "開発チームを増やす", A, 1.2, 8.5)
 + _b(268, 220, 236, 30, "非機能要件で開発単位を分ける", A, 1.2, 8.5)
 + _b(516, 220, 244, 30, "スケールさせる機能を切り離す", A, 1.2, 8.5)
 + _t(20, 268, "大きさ自体は重要ではない ── 基準は「モデルが役に立つかどうか」", M, 9)
 + _t(20, 288, "だから切り方の違いは、好みではなく 事情の違い として現れる", K, 9, bold=True)
 + '</svg>',
 '<b>上限は言葉で決まり、内側の割り方は事情で決まる。</b>'
 '同じ言葉が一貫する<b>もっとも広い範囲</b>が上限で、それを超えると同じ語が2つの意味を持ちはじめる ── ここは動かせない。'
 'その内側をどこまで割るかは設計判断で、原典が挙げる理由は3つ（開発チームを増やす ・ 非機能要件 ・ スケールさせる機能の切り離し）。'
 '<b>だから「どちらが正しい切り方か」は決まらない</b> ── 上限を超えていないか、割る理由があるか、だけが問える。')

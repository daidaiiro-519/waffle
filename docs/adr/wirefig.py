def _b(x,y,w,h,lines,stroke,sw=1.3,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="none" stroke="{stroke}" stroke-width="{sw}"{d}/>'
    n=len(lines); cy=y+h/2-(n-1)*7.5+3.5
    for i,(t,sz,bold) in enumerate(lines):
        fw=' font-weight="700"' if bold else ""
        o+=(f'<text x="{x+w/2}" y="{cy+i*15}" text-anchor="middle" font-size="{sz}" fill="{stroke}"{fw}>{t}</text>')
    return o
def _t(x,y,s,tone="var(--muted)",size=9,anchor=None,bold=False):
    a=f' text-anchor="{anchor}"' if anchor else ""
    fw=' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'
def _a(x1,y1,x2,y2,tone="var(--key)",dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{tone}" stroke-width="1.3"{d} marker-end="url(#wa)"/>'
K,M,D,C,W="var(--key)","var(--muted)","var(--dim)","currentColor","var(--warn)"
AR=('<defs><marker id="wa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

WIRE=('<svg viewBox="0 0 720 356" role="img" aria-label="brainstormは役だけを宣言し、skill-routerの配線表が役に実際のSkillを当てる">'
 + AR
 + _t(20,16,"brainstorm が宣言するのは「役」だけ。何を当てるかは、配線表が持つ",K,10,bold=True)
 + _t(20,42,"brainstorm が宣言する役",K,8.5,bold=True)
 + _t(268,42,"skill-router の配線表",K,8.5,bold=True)
 + _t(500,42,"当てられた Skill（差し替えられる）",K,8.5,bold=True)
 + _b(20,52,220,44,[("原典を落とす役",9,True)],C)
 + _b(268,52,190,44,[("配線あり",8.5,True)],K,1.4)
 + _b(490,52,210,44,[("source-fidelity",9,True)],K,1.4)
 + _a(240,74,264,74) + _a(458,74,486,74)
 + _b(20,110,220,44,[("案を敵対的に確かめる役",9,True)],C)
 + _b(268,110,190,44,[("配線あり",8.5,True)],K,1.4)
 + _b(490,110,210,44,[("ddd-advisor ほか",9,True)],K,1.4)
 + _a(240,132,264,132) + _a(458,132,486,132)
 + _b(20,168,220,44,[("利用者が足した役",9,True)],C,1.3,"5 4")
 + _b(268,168,190,44,[("ここに1行足すだけ",8.5,True)],W,1.4,"5 4")
 + _b(490,168,210,44,[("好きな Skill",9,True)],W,1.4,"5 4")
 + _a(240,190,264,190,W,"4 3") + _a(458,190,486,190,W,"4 3")
 + _t(20,238,"配線が無い役は、飛ばす",K,9.5,bold=True)
 + _b(20,250,680,42,[("brainstorm は止まらない ── 原文を自分で落として手元に残し、その札を付ける",8.5,False)],M,1.1)
 + _t(20,320,"だから brainstorm は、どの Skill の名前も持たない ── 持ち出しても、箱は閉じたままである",K,9,bold=True)
 + _t(20,342,"source-fidelity は「原典を落とす役」に当てられた1つの実装にすぎず、別のものへ差し替えられる",M,9)
 + '</svg>', '')

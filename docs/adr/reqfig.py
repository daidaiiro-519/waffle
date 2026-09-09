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
def _a(x1,y1,x2,y2,tone="var(--key)"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{tone}" stroke-width="1.4" marker-end="url(#ra)"/>'
K,M,D,C,W="var(--key)","var(--muted)","var(--dim)","currentColor","var(--warn)"
AR=('<defs><marker id="ra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

FLOW=('<svg viewBox="0 0 720 348" role="img" aria-label="三種の出どころが突き合わせに入り、支えられない案が落ちて、残った1つが答えになる">'
 + AR
 + _t(20,14,"根拠になれるのは、三種の出どころだけ",K,10,bold=True)
 + _b(20,26,200,54,[("原典",9.5,True),("外にある文献 ・ 規格 ・ 実装",8.5,False)],C)
 + _b(255,26,200,54,[("決まり",9.5,True),("この盤面で決着した論点",8.5,False)],C)
 + _b(490,26,210,54,[("実測",9.5,True),("このリポジトリを数えた結果",8.5,False)],C)
 + _b(20,94,200,30,[("取り方が、書かれていない",8.5,True)],W,1.2,"5 4")
 + _a(120,124,244,156,W)
 + _a(355,80,355,156)
 + _a(595,80,472,156)
 + _b(200,158,320,52,[("突き合わせ",9.5,True),("この案は、どの札で支えられるか",8.5,False)],K,1.6)
 + _a(300,210,180,246,D)
 + _a(420,210,540,246)
 + _b(20,248,300,50,[("支えられない案は落とす",9,True),("名前と『何が壊れるか』を残す",8.5,False)],D)
 + _b(390,248,310,50,[("残った1つが、答えになる",9,True),("札つきの根拠が、そのまま付いてくる",8.5,False)],K,1.6)
 + _t(20,326,"札に当たらないものは、根拠として置かない ── 置けば、確かめようのないものが決まりになる",K,9,bold=True)
 + '</svg>', '')

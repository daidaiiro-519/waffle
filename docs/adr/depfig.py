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
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{tone}" stroke-width="1.4"{d} marker-end="url(#da)"/>'
K,M,D,C,W="var(--key)","var(--muted)","var(--dim)","currentColor","var(--warn)"
AR=('<defs><marker id="da" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

DEPS=('<svg viewBox="0 0 720 424" role="img" aria-label="道具は内側で閉じていて、外に在るのは材料だけという依存の形">'
 + AR
 + _t(20,16,"外に在るのは材料だけで、道具は内側で閉じている",K,10,bold=True)
 + _b(20,30,210,44,[("原典 ── 外の文献 ・ 規格",9,True)],C)
 + _t(20,92,"落として保存すると、内側に残る",M,8.5)
 + _t(20,108,"いま14件（sha256と日付つき）",M,8.5)
 + _b(490,30,210,44,[("advisor の knowledge 22件",9,True)],D)
 + _t(490,92,"在れば使う。無くても止まらない",D,8.5)
 + _t(490,108,"持ち出すと、ここは切れる",D,8.5)
 + _b(180,126,360,182,[],K,1.8)
 + _t(360,146,"brainstorm ── このまま持ち出せる単位",K,9.5,"middle",True)
 + _b(196,158,110,30,[("SKILL.md",8,False)],C,1)
 + _b(314,158,110,30,[("build_board.py",8,False)],C,1)
 + _b(432,158,94,30,[("figcheck.py",8,False)],C,1)
 + _b(196,196,110,30,[("serve.py",8,False)],C,1)
 + _b(314,196,212,30,[("answer-sheet.schema.json",8,False)],C,1)
 + _t(360,250,"標準ライブラリだけ ── 外部パッケージ 0",K,9,"middle",True)
 + _t(360,270,"別のリポジトリへ、この箱ごと持っていける",M,8.5,"middle")
 + _t(360,290,"成果物の HTML は書体を外から読むが、読めなくても崩れない",M,8,"middle")
 + _b(20,346,210,44,[("対象のリポジトリ ── 実測",9,True)],C)
 + _t(20,408,"その場のリポジトリを数える。どこにでも在る",M,8.5)
 + _b(490,346,210,44,[("Claude Code の Hook",9,True)],D)
 + _t(490,408,"無ければ「読んで」の一言で回る",D,8.5)
 + _a(130,74,176,146)
 + _a(596,74,546,146,D,"5 4")
 + _a(130,346,176,300)
 + _a(596,346,546,300,D,"5 4")
 + '</svg>', '')

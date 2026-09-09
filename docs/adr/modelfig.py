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
K,M,D,C,W="var(--key)","var(--muted)","var(--dim)","currentColor","var(--warn)"
AR=('<defs><marker id="ma" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

MODEL=('<svg viewBox="0 0 720 344" role="img" aria-label="いまの欄はWaffleの分類を含むが、役で書き直すとWaffleの語が消える">'
 + AR
 + _t(20,16,"いまの欄",D,9.5,bold=True)
 + _b(20,26,290,196,[],D,1.4)
 + _b(36,40,258,26,[("skill：実務Skill の名",8.5,False)],D,1)
 + _b(36,72,258,26,[("purpose：どの仕様書か",8.5,False)],D,1)
 + _b(36,104,258,26,[("combinedSkills：advisor だけ",8.5,False)],W,1.2)
 + _b(36,136,258,26,[("strength：必須 ／ 推奨",8.5,False)],W,1.2)
 + _b(36,168,258,26,[("advisorBoundaries：advisor 間の委譲",8.5,False)],W,1.2)
 + _t(20,240,"『実務Skill』『advisor』という Waffle の分類が、",W,8.5)
 + _t(20,256,"欄の意味そのものに入っている ── 語ごと合わない",W,8.5)
 + f'<line x1="322" y1="120" x2="378" y2="120" stroke="{K}" stroke-width="1.6" marker-end="url(#ma)"/>'
 + _t(350,110,"同じ8行が",K,8,"middle")
 + _t(350,140,"そのまま書ける",K,8,"middle")
 + _t(392,16,"役で書くと",K,9.5,bold=True)
 + _b(392,26,308,196,[],K,1.7)
 + _b(408,40,276,26,[("役：必要とされる能力",8.5,False)],C,1)
 + _b(408,72,276,26,[("要求元：それを必要とする場面",8.5,False)],C,1)
 + _b(408,104,276,26,[("担い手：当てられた Skill（複数可）",8.5,False)],C,1)
 + _b(408,136,276,26,[("無いとき：止める ／ 参考 ／ 飛ばす",8.5,False)],C,1)
 + _t(550,186,"欄は4つ。これだけ",K,9,"middle",True)
 + _t(392,240,"Waffle の語が1つも出てこない ── だから",K,8.5)
 + _t(392,256,"別のプロジェクトでも、そのまま使える",K,8.5)
 + f'<line x1="20" y1="284" x2="700" y2="284" stroke="var(--rule)"/>'
 + _t(20,306,"「advisor だけを当てる」は、モデルではなく、このリポジトリの慣習として表の中に降りる",K,9,bold=True)
 + _t(20,328,"だから表は1つでよい ── 2つに分けようとしたのは、悪い抽象を前提にしていたからだった",M,9)
 + '</svg>', '')

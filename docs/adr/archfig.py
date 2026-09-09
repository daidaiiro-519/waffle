def _b(x,y,w,h,lines,stroke,sw=1.3,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="none" stroke="{stroke}" stroke-width="{sw}"{d}/>'
    n=len(lines); cy=y+h/2-(n-1)*7+3.5
    for i,(t,sz,bold) in enumerate(lines):
        fw=' font-weight="700"' if bold else ""
        o+=(f'<text x="{x+w/2}" y="{cy+i*14}" text-anchor="middle" font-size="{sz}" '
            f'fill="{stroke}"{fw}>{t}</text>')
    return o
def _t(x,y,s,tone="var(--muted)",size=9,anchor=None,bold=False):
    a=f' text-anchor="{anchor}"' if anchor else ""
    fw=' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{tone}"{a}{fw}>{s}</text>'
def _a(x1,y1,x2,y2,tone="var(--key)"):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{tone}" stroke-width="1.4" marker-end="url(#aa)"/>'
K,M,D,C,W="var(--key)","var(--muted)","var(--dim)","currentColor","var(--warn)"
AR=('<defs><marker id="aa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
    'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--key)"/></marker></defs>')

ARCH=('<svg viewBox="0 0 760 412" role="img" aria-label="回答が画面からファイルへ落ち、フックを通って私に届き、盤面が更新されて画面へ戻る循環">'
 + AR
 + _t(20,16,"ローカル ── 書き込める",K,10,bold=True)
 + _b(20,30,170,50,[("承認の画面",9.5,True),("approval-only-simulator.html",7.5,False)],C)
 + _b(240,30,170,50,[("serve.py",9.5,True),("配る ＋ 受け取る",8.5,False)],C)
 + _b(460,30,170,50,[("回答 1件",9.5,True),(".waffle/answers/*.json",7.5,False)],C)
 + _a(192,55,238,55) + _t(215,48,"①",K,8.5,"middle")
 + _a(412,55,458,55) + _t(435,48,"② POST",K,8,"middle")
 + _b(460,96,170,28,[("answer-sheet.schema.json",7.5,False)],M,1.1,"4 3")
 + f'<line x1="545" y1="80" x2="545" y2="96" stroke="{M}" stroke-width="1"/>'
 + _t(646,114,"形だけ検査する",M,8)
 + f'<line x1="0" y1="150" x2="760" y2="150" stroke="{W}" stroke-width="1.2" stroke-dasharray="6 5"/>'
 + _t(20,144,"ここから下は、あなたが何か書くまで動かない",W,9,bold=True)
 + _b(460,172,170,50,[("UserPromptSubmit",9,True),("未読の回答だけ渡す",8.5,False)],K,1.5)
 + _a(545,124,545,170) + _t(560,166,"③",K,8.5)
 + _b(240,172,170,50,[("Claude Code のセッション",8.5,True),("承認を反映し、差し戻しに答える",7.5,False)],K,1.6)
 + _b(20,172,170,50,[("盤面 ・ spec",9.5,True),("更新される正本",8.5,False)],C)
 + _a(458,197,412,197) + _t(435,190,"④",K,8.5,"middle")
 + _a(238,197,192,197) + _t(215,190,"⑤",K,8.5,"middle")
 + _a(105,170,105,82) + _t(120,130,"⑥ 画面を作り直す",K,8.5)
 + f'<line x1="0" y1="246" x2="760" y2="246" stroke="var(--rule)"/>'
 + _t(20,268,"Artifact ── 外から書き込めない",D,10,bold=True)
 + _b(20,282,170,46,[("同じ画面",9.5,True),("claude.ai の Artifact",7.5,False)],D)
 + _b(240,282,150,46,[("写す",9.5,True),("JSON を作る",8.5,False)],D)
 + _b(440,282,150,46,[("会話へ貼る",9.5,True)],D)
 + _b(580,352,0,0,[],D)
 + _a(192,305,238,305,D) + _a(392,305,438,305,D)
 + f'<line x1="590" y1="305" x2="640" y2="305" stroke="{D}" stroke-width="1.4"/>'
 + f'<line x1="640" y1="305" x2="640" y2="212" stroke="{D}" stroke-width="1.4" marker-end="url(#aa)"/>'
 + _t(654,262,"同じセッションへ入る",D,8)
 + _t(20,352,"どちらの道でも、私が動き出すのはあなたが何か書いたときだけ ── 違うのは、書くのが本文か「読んで」の一言か",K,9,bold=True)
 + _t(20,374,"回答ファイルは1件ごとに残る。承認したもの ・ 差し戻したもの ・ 書いたことが、あとから順に読める",M,9)
 + _t(20,394,"schema が見るのは形だけ（諾否は3値、差し戻しの理由は3値）── 中身が妥当かは、私とあなたが決める",M,9)
 + '</svg>', '')

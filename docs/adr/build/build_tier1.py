import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, extra

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="13" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
def gsvg(vb,inner,cap):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

b=''
b+='<rect x="16" y="30" width="300" height="228" rx="4" fill="none" stroke="var(--assume)" stroke-width="1" stroke-dasharray="4 3"/>'
b+='<text x="24" y="22" font-size="11" fill="var(--assume)">段1 ── 部品を提供する</text>'
b+=gb(34,48,264,42,"表紙",None,"var(--assume)")
b+=gb(34,100,264,42,"構造の文法 6つ",None,"var(--assume)",True)
b+=gb(34,152,264,42,"標準の組み立て（図・木）",None,"var(--assume)")
b+=gb(34,204,264,42,"指針と、成果物への落とし方",None,"var(--assume)")
b+='<rect x="404" y="30" width="300" height="228" rx="4" fill="none" stroke="var(--infer)" stroke-width="1" stroke-dasharray="4 3"/>'
b+='<text x="412" y="22" font-size="11" fill="var(--infer)">段2 ── 組み合わせて表現する</text>'
b+=gb(422,48,264,42,"137のブロック",None,"var(--infer)")
b+=gb(422,100,264,42,"6つの鍵と31の枝",None,"var(--infer)")
b+=gb(422,152,264,42,"623本の記入の指針",None,"var(--infer)")
b+=gb(422,204,264,42,"描き方と宛先の中身",None,"var(--infer)")
for y in (69,121,173,225): b+=ga(300,y,420,y)
b+='<text x="360" y="16" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">使って組む</text>'
FIG=gsvg("0 0 720 272",b,
 "<b>段1 は、このスキーマが表現できる部品を全て提供する。段2 は、それを組み合わせて、その型を表現する。</b>"
 "数えなくても判定でき、型が1本増えても答えが変わらない。")

grammar = tbl(["部品","何を組めるか"],[
 ("",["<b>値</b>","文字・数・真偽・時刻"]),
 ("",["<b>まとまり</b>","名前つきの欄の集まり"]),
 ("",["<b>並び</b>","同じ形の繰り返し"]),
 ("keyrow",["<b>入れ子</b>","まとまりの中のまとまり。<b>深さは有界</b>"]),
 ("keyrow",["<b>選び</b>","どの形になるかが、ある欄の値で決まる"]),
 ("",["<b>名前で共有</b>","同じ形を、名前を付けて何度でも使う"]),
])

layers = tbl(["層","何か","例","持ち主"],[
 ("keyrow",["<b>文法</b>","組み立てるための語","まとまり・並び・入れ子","<b>段1</b>"]),
 ("keyrow",["<b>標準の組み立て</b>","段1 が名前付きで提供する既製品","<b>図・木</b>","<b>段1</b>"]),
 ("",["型ごとの組み立て","その型が組むもの","<code>TitleBlock</code>・原文・受け入れ基準","段2"]),
])

idx = tbl(["","本来はどうあるべきか","いまどうなっているか"],[
 ("keyrow",["何を持つか","<b>その文書に何が書かれているかの要約</b>","この型のブロックをどう読むかの指針"]),
 ("keyrow",["何から作るか","<b>その文書の中身</b>","<code>x-prompt-query</code> の写し"]),
 ("keyrow",["文書ごとに","違う","<b>同じ型なら完全に同一</b>"]),
 ("",["何のためか","全文を読まずに当たりを付け、必要な鍵だけ引く","<b>その目的を果たしていない</b>"]),
])

body="".join([
 '<header><p class="eyebrow">段1 の共通契約</p>'
 '<h1>段1 は何を提供し、段2 は何を組むか</h1>'
 '<p class="lede">実測から部品を拾い上げるのをやめ、<b>必要から導いた</b>。'
 '実測は、この立て方から漏れているものを探すためだけに使う。</p></header>',

 sec("01","線引き",
   "<b>段1 は部品を提供し、段2 はそれを組み合わせる。</b>"
   "「全型に共通なら上位」より良い基準である──数えなくても判定でき、型が1本増えても答えが変わらない。",
   FIG),

 sec("02","段1 が提供するもの",
   "段2 が「この型はこういう文書だ」と書けるために、4つが要る。",
   tbl(["群","なぜ要るか"],[
     ("keyrow",["<b>表紙</b>",
       "Document はエンティティである。<b>識別子・型・版・状態・時刻・役どころ</b>は型に依らない"]),
     ("keyrow",["<b>構造の文法</b>","中身を組み立てるため。<b>6つ</b>（次の節）"]),
     ("",["<b>書き方と読み方</b>","構造の各所に添える指針"]),
     ("",["<b>成果物への落とし方</b>","描き方と宛先"]),
   ]) +
   '<h3 class="sub-h">構造の文法 ── 6つ</h3>' + grammar +
   '<p class="blob">必須・決め打ち・選択肢・最小の個数・閉じる、といった<b>制限は、この6つに掛かる修飾</b>であって、'
   '独立した部品ではない。</p>'),

 sec("03","部品には2つの層がある",
   "ここを混ぜていた。<b>図と木が段1 なのは、文法が足りないからではない。</b>",
   layers,
   fold("なぜ図と木が段1 なのかを開く",
     '<p class="blob">文法だけでも組める。しかし<b>意味がどの型でも同じでなければ困る</b>。'
     '図の16の主張が型ごとに違ったら、図が図でなくなる。'
     'だから段1 が、名前の付いた既製品として持つ。</p>'
     '<p class="blob"><b><code>KnowledgeSchema</code> と <code>SkillSchema</code> が、'
     '同じ「深さ有界の木」を別々の名前で自前に組んでいた。</b>'
     '概念の木と、手順の親子である。2本が独立に同じものを作っているのは、既製品が無かったことの現れ。</p>'
     '<p class="foldnote">ここから規則が1つ出る ── '
     '<b>段1 が提供していない部品を段2 が自前で作っていたら、それは段1 の欠落である。</b>'
     'これは機械で確かめられる。</p>')),

 sec("04","<code>_index</code> は、いまの姿と本来の姿が別物だった",
   "別々の文書の索引を比べたら、<b>12ブロックとも完全に同一</b>だった。"
   "中身は読み方の指針の写しで、その文書について何も語っていない。",
   idx,
   fold("測り方と、決定との食い違いを開く",
     '<p class="blob"><code>uc-render-document</code> と <code>uc-check-scenario-drift</code> の索引を比べた。'
     '共通するブロック12件のうち、<b>12件とも中身が1文字も違わなかった</b>。</p>'
     '<p class="blob">承認済みの決定は「<b><code>x-*</code> は型に置き、実体へは写さない</b>」と定めている。'
     '<code>_index</code> は <code>x-prompt-query</code> から作られて実体に住むので、'
     '<b>まさに写している</b>。型の指針を直すと、索引が古くなる。</p>'
     '<p class="foldnote">落とすのではなく、作り直す ── '
     '<b>その文書の中身から作る要約</b>として定義し直す。</p>')),

 sec("05","この立て方で、まだ決めていないこと",
   "部品の一覧を確定させる前に、決めることが残っている。",
   tbl(["項目","何を決めるか"],[
     ("keyrow",["<code>_index</code> の作り直し","文書の中身から作る要約として定義し直すか"]),
     ("keyrow",["部品の確定","上の立て方で一覧を閉じ、実測で漏れを検査する"]),
     ("",["決定に「置き換えられた」を入れるか",
       "入れないと、古い決定が承認済みのまま残る。この作業で実際に起きた"]),
     ("",["図の置き場所の決定","未承認のまま。段1 の仕様の入力になる"]),
   ])),

 sec("06","実測は、どう使ったか",
   "<b>部品を拾い上げるためには使っていない。</b>この立て方から漏れているものを探すために使う。",
   tbl(["測ったこと","何が分かったか"],[
     ("",["ブロック137種の分布","<b>127種は1本の型にしか現れない</b>。ブロックはほぼ全部が段2 の持ち物"]),
     ("",["型と制限の使われ方","型は4つで99.5%。<code>format</code> は日時のみ、<code>pattern</code> は1回"]),
     ("keyrow",["分岐の形","<b>6つの鍵すべてが同じ形</b>──ある欄の値で必須ブロックの集合が変わる"]),
     ("keyrow",["自前で組まれた部品","<b>図と木が、段1 に無いために段2 で組まれていた</b>"]),
     ("",["使われている鍵","628種のうち、言語として働くのは29語。残りは欄の名前"]),
   ]),
   fold("この整理に至るまでに、私が外したこと",
     '<p class="blob"><b>鍵を数えて一覧に足していく、をやっていた。</b>'
     'そのやり方だと、実装の事情がそのまま語彙になる。'
     '「7語」という数も、測定から私が計算して会話で言い、計画に書き写しただけで、'
     '<b>決定していなかった</b>。</p>'
     '<p class="foldnote">実測は方針の根拠にしない。'
     '<b>方針が正で、実測はそれに照らして判定される対象である。</b></p>')),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
"""
html=("<title>段1 は何を提供し、段2 は何を組むか</title>"
      f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/tier1-parts.html").write_text(html,encoding="utf-8")
print("書いた",len(html))

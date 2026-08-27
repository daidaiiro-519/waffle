import sys, pathlib
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, step, joint, extra
C=lambda s: f"<code>{s}</code>"
FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="12.5" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
def gt(x,y,t,c="var(--ink-faint)",sz=10.5,anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{sz}" fill="{c}">{t}</text>'
def gsvg(vb,inner,cap,minw="44rem"):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:{minw};width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

# --- FIG1: 4段の順序 ---
a=''
X=[14,214,414,614]; W=182
lbl=[("1 段1 を起こす","部品を用意する"),("2 型を版として起こす","8つを組み直す"),
     ("3 文書を型ごとに移す","1つ閉じてから次へ"),("4 旧い版を落とす","閉じ切った型から")]
touch=["文書に触れない","文書に触れない","文書に触れる","文書に触れない"]
for i,(t,s) in enumerate(lbl):
    a+=gb(X[i],48,W,52,t,s,"var(--against)" if i==2 else "var(--infer)",i==2)
    a+=gt(X[i]+W/2,120,touch[i],"var(--against)" if i==2 else "var(--ink-faint)",10.5,"middle")
    if i<3: a+=ga(X[i]+W,74,X[i+1],74)
a+=gt(14,26,"部品が無ければ型は組めず、型が無ければ文書は移せない","var(--ink-soft)",11)
a+=gt(14,152,"書き換えが起きるのは第3段だけ。ここだけが、途中で止まると新旧が混ざる","var(--against)",10.5)
FIG1=gsvg("0 0 810 168",a,
 "<b>順序は、承認済みの「段1が部品を提供し、段2が組み立てる」から出る。</b>"
 "文書に触れるのは第3段だけである。")

# --- FIG2: 段1 だけは範囲を絞れない ---
b=''
b+=gt(14,20,"型は8つに絞れる ── 第2段・第3段は、範囲の内側で閉じる","var(--infer)",11)
b+=gb(14,34,150,44,"段2（8つ）","組み直す","var(--infer)",True)
b+=ga(164,56,236,56)
b+=gb(236,34,150,44,"その文書 179本","移す","var(--infer)")
b+=gt(14,116,"段1 は絞れない ── 全型の共通契約","var(--against)",11)
b+=gb(14,130,150,44,"段1","全型の共通契約","var(--against)",True)
b+=ga(164,140,236,124)
b+=gb(236,102,150,44,"範囲内 179本",None,"var(--infer)")
b+=ga(164,162,236,178)
b+=gb(236,156,150,44,"範囲外 37本","古い形のまま","var(--against)",True)
b+=gt(400,182,"読めなくなると、ここが壊れる","var(--against)")
FIG2=gsvg("0 0 700 212",b,
 "<b>型は8つに絞れるが、段1 は絞れない。</b>"
 "範囲外の37本は<b>古い型のまま</b>残るので、"
 "<b>段1 はそれを読んで判定・描画できなければならない</b>。"
 "ただし<b>古い宣言を起こせる必要は無い</b> ── 旧い型は既に型として在り、起こす相手がいない。")

scope = tbl(["区分","本数","扱い"],[
 ("keyrow",["<b>今回の範囲</b>","<b>179</b>",
   "<code>DomainSpec</code> 44／<code>Knowledge</code> 78／<code>Skill</code> 20／"
   "<code>Hook</code> 15／<code>Coding</code> 13／<code>Template</code> 6／<code>Agent</code> 3"]),
 ("keyrow",["<b>今回の範囲外</b>","<b>11</b>",
   "<code>Platform</code> のみ。<b>廃止して考え直す</b>ので、古い形のまま残る"]),
 ("",["触らない（<code>bc-artifact-share</code>）","26","そのまま"]),
 ("",["廃止（Handoff）","37","落とす"]),
 ("keyrow",["<b>合計</b>","<b>253</b>","—"]),
])

types = tbl(["型","文書","いまの版","この移行で変わるもの","難しさ"],[
 ("keyrow",["<code>DomainSpecSchema</code>","<b>44</b>","v11／v10／v8 が併存",
   "<b>工程の状態を落とす</b>／種別の鍵／枝ごとの中身","<b>大。旧版を落とし切れない</b>"]),
 ("keyrow",["<code>KnowledgeSchema</code>","<b>78</b>","<b>v5 が57本、v6 が21本</b>",
   "部品での組み直し","<b>大。前の移行が終わっていない</b>"]),
 ("",["<code>SkillSchema</code>","20","v2","部品での組み直し","中"]),
 ("",["<code>HookSchema</code>","15","v1","部品での組み直し","小"]),
 ("",["<code>CodingSchema</code>","13","v7","部品での組み直し","中"]),
 ("keyrow",["<code>TemplateSchema</code>","<b>6</b>","v2",
   "部品での組み直し。<b>ただし実際に使われているテンプレートは17本で、型を持つのは6本だけ</b>",
   "<b>中。6本のままか17本へ広げるかを、先に決める</b>"]),
 ("",["<code>AgentSchema</code>","3","v3","部品での組み直し","小"]),
 ("keyrow",["<b>ADR</b>","<b>0</b>","<b>型が無い</b>",
   "<b>新しく起こす。</b>いま21枚が文書の外にあり、手で書いた組み立てで描かれている",
   "<b>中。移すのではなく作る</b>"]),
])

why = (step("premise","前提","承認済みの決定が<b>「段1が部品を提供し、段2が組み立てる」</b>と定めている")
 + joint("だから")
 + step("conclude","言えること","<b>部品が無ければ型は組めない。</b>段1 が型に先立つ")
 + joint("文書の側も見た")
 + step("premise","前提","文書は自分の型を <code>schemaRef</code> で指し、その型に照らして判定される")
 + joint("だから")
 + step("conclude","言えること","<b>型が無ければ文書は移せない。</b>型が文書に先立つ")
 + joint("落とす側は")
 + step("conclude","結論","<b>旧い版は、その型の文書が全部移り終えてから落とす。</b>"
        "先に落とすと、移していない文書が判定できなくなる")
 + joint("裏づけを取った")
 + step("evidence","測った","<code>DomainSpecSchema</code> は <b>v8・v10・v11 が同時に生きている</b>。"
        "<b>版の併存は、新しく持ち込む仕組みではない</b>"))

stat = tbl(["いまの値","本数","持っている型","移した後"],[
 ("keyrow",["<b>VALIDATED</b>（工程）","<b>69</b>","<code>DomainSpecSchema</code> のみ",
   "<b>成熟の値へ</b>。うち範囲内は <b>44本</b>"]),
 ("",["CREATED（工程）","1","同上","範囲外（<code>bc-artifact-share</code>）"]),
 ("keyrow",["<b>RENDERED</b>（工程）","<b>0</b>","宣言だけある","<b>使われていない</b>"]),
 ("keyrow",["<b>SUPERSEDED</b>（工程）","<b>0</b>","宣言だけある","<b>使われていない</b>"]),
 ("",["ACTIVE / DRAFT / DEPRECATED（成熟）","135",
   "<code>Knowledge</code>・<code>Skill</code>・<code>Hook</code>・<code>Coding</code>・"
   "<code>Template</code>・<code>Agent</code> の6つ","<b>そのまま</b>"]),
])

risk = tbl(["危ないところ","なぜ","どうするか"],[
 ("keyrow",["<b>段1 だけは範囲を絞れない</b>",
   "<b>全型の共通契約</b>なので、範囲外の <code>Platform</code> 11本と触らない26本にも当たる",
   "<b>段1 が旧い型を読んで判定・描画できること</b>を第1段の条件に入れる。"
   "<b>起こせる必要は無い</b>"]),
 ("keyrow",["<b><code>TemplateSchema</code> の範囲が決まっていない</b>",
   "<b>17本のうち6本しか型を持たない。</b>無いほうに "
   "<code>template-judgment-platform</code>・<code>template-judgment-ux</code> が含まれ、"
   "<b>それは廃止して考え直すと決めた2領域である</b>",
   "<b>先に6本か17本かを決める。</b>17本なら、その2本は後回しにできる"]),
 ("keyrow",["<b><code>KnowledgeSchema</code> の前の移行が終わっていない</b>",
   "<b>v5 に57本、v6 に21本</b>。今回の移行と、v5→v6 の未完の移行が重なる",
   "<b>先に v6 へ揃えてから、この移行に入れる</b>"]),
 ("keyrow",["<b><code>DomainSpecSchema</code> の旧版は落とせない</b>",
   "v10 と v8 を指す26本が <code>bc-artifact-share</code> にあり、<b>触らないと決めてある</b>",
   "<b>開いたままにする。</b>閉じたことにしない"]),
 ("",["ADR は移すものが無い","文書が0本で、<b>21枚は文書の外</b>にある。"
   "描いているのは手で書いた組み立てで、<b>型からの描画ではない</b>",
   "<b>作ってから、既にある21枚を入れる</b>"]),
 ("",["第3段の途中で止まると新旧が混ざる","書き換えが起きるのはここだけ",
   "<b>型ひとつを閉じ切ってから次へ。</b>複数を同時に開かない"]),
])

close = tbl(["単位","終わったと言える条件"],[
 ("keyrow",["<b>型ひとつ</b>","その型を指す文書が<b>全部</b>新しい版になり、<b>旧い版が落ちた</b>とき"]),
 ("keyrow",["<b>今回</b>","<b>8つの型が段2 として立ち、179本が移り終えたとき</b>"]),
 ("",["全体","<b>言えない。</b>範囲外の11本と、触らない26本が古い形のまま残る"]),
])

later = tbl(["型","なぜ今回でないか"],[
 ("keyrow",["<code>PlatformSpec</code>（11本）","<b>廃止して考え直す</b>と決めた。"
   "土台は DDD ではなく、<b>操作の契約が運べないほうの半分</b>に置ける見込みがある"]),
 ("keyrow",["<code>PresentationSpecSchema</code>（0本）","<b>同上。</b>"
   "<b>domain に従属する</b>ので、domain より先には安定しない"]),
])

open_q = tbl(["項目","何が決まっていないか","いつ決まるか"],[
 ("keyrow",["<b>ADR の型が何を宣言するか</b>",
   "<b>21枚から起こすのか、決めてから当てるのか。</b>いまの21枚は形が揃っていない"
   "（承認の節が無いものが2枚ある）","<b>第2段の入口</b>"]),
 ("keyrow",["<b>図の仕様</b>",
   "<b>型ではないので、8つのどれにも入らない。</b>"
   "図は<b>段1 が持つ部品</b>なので、<code>$defs.Figure</code> を書き出すのは段1 自身である",
   "<b>第1段の中。</b>段1 の実装より前"]),
 ("",["各語の名前","この計画では仮のまま","仕様を書くとき"]),
 ("",["範囲外の11本をいつ移すか","次の回か、さらに先か","この移行が閉じたあと"]),
])

body="".join([
 '<header><p class="eyebrow">移す計画</p>'
 '<h1>8つの型を段2 として立て、179本を移す</h1>'
 '<p class="lede">今回立てるのは <b>domain・knowledge・skill・hook・coding・template・agent・ADR</b> の8つ。'
 '書き換えが起きるのは<b>4段のうち1段だけ</b>で、互換は<b>版の併存</b>で保つ ── '
 'ただし<b>段1 だけは範囲を絞れない</b>。</p></header>',

 sec("01","何を書き換えるか",
   "<b>253本のうち、今回移すのは179本</b>である。",
   scope,
   fold("範囲の外に置いた3つ",
     '<p class="blob"><b><code>bc-artifact-share</code> の26本</b>は触らないと決めてある。'
     '<b>Handoff の37本</b>は ADR へ置き換え済みで、移す先が無い。'
     '<b>ほか11本</b>は、型そのものを考え直すと決めたものである。</p>'
     '<p class="foldnote">この3つは理由が違う。'
     '<b>触らない・落とす・後回しにする</b>は、閉じ方も違う ── 節07を見よ。</p>')),

 sec("02","立てる8つ",
   "<b>7つは移すもの、ADR だけは作るもの</b>である。",
   types),

 sec("03","順序",
   "<b>4段。書き換えが起きるのは第3段だけ</b>である。",
   FIG1 + why),

 sec("04","段1 だけは範囲を絞れない",
   "<b>型は5つに絞れる。段1 は絞れない。</b>",
   FIG2,
   fold("なぜ段1 だけ違うのか",
     '<p class="blob">段2 は<b>型ごとに独立している</b>ので、5つだけ組み直しても'
     '残りは古い型のまま成り立つ。<b>段1 は全型の共通契約</b>なので、入れ替えると'
     '<b>範囲外の37本が読めなくなる</b>。</p>'
     '<p class="foldnote">したがって第1段の条件は「新しい部品を用意する」だけでは足りない。'
     '<b>旧い型を読んで判定・描画できたままにする</b>ことが要る。'
     'ただし<b>旧い宣言を起こせる必要は無い</b> ── 旧い型は既に型として在るので、'
     '起こす相手がいない（段1 の仕様 節07）。</p>'
     '<p class="foldnote">これは後方互換を賄うことではなく、'
     '<b>範囲を絞ると決めたことの代償</b>である。</p>')),

 sec("05","状態は、実質ひとつの値しか取っていない",
   "<b>工程の4つの値のうち、実際に使われているのは2つだけ</b>である。",
   stat,
   fold("この測定が計画を軽くする",
     '<p class="blob"><b><code>RENDERED</code> と <code>SUPERSEDED</code> は1本も無い。</b>'
     '<code>CREATED</code> も1本だけで、それは範囲外にある。</p>'
     '<p class="foldnote">つまり範囲内の44本は<b>すべて <code>VALIDATED</code> 一色</b>である。'
     '<b>値ごとの対応表を作る必要が無く、落ちる情報も無い。</b></p>')),

 sec("06","危ないところ",
   "<b>6つ。うち2つは範囲の決め方から生まれた</b>。",
   risk),

 sec("07","終わったと言える条件",
   "<b>全体を閉じ切ることはできない。</b>今回閉じるのは8つの型だけである。",
   close),

 sec("08","今回でない型",
   "<b>2つだけ。どちらも廃止して考え直す。</b>",
   later),

 sec("09","答えないこと",
   "4つ残る。<b>いずれも先の段で決まる。</b>",
   open_q),

 sec("10","承認", None,
   '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-17 承認。段1 の条件を実際に要るものへ合わせたうえで</span>'
   '<span class="m">2026-08-16 範囲を8つの型に広げて書き直し</span></div>'),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>8つの型を段2 として立て、179本を移す</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/migration-plan.html").write_text(out,encoding="utf-8")
print("書いた",len(out))

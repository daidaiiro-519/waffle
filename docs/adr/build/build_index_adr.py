import sys, json, pathlib, html
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
e=html.escape
before=pathlib.Path(S+"/idx_before.json").read_text(encoding="utf-8")
after=pathlib.Path(S+"/idx_after.json").read_text(encoding="utf-8")

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="13" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+15}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2,lb=None,lx=None,ly=None):
    o=f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
    if lb: o+=f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="10.5" fill="var(--ink-faint)">{lb}</text>'
    return o
def gsvg(vb,inner,cap):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

a=''
a+='<text x="14" y="18" font-size="11" fill="var(--against)">変更前 ── 型の指針を写して、文書の中に保存する</text>'
a+=gb(14,30,168,44,"型の読み方の指針",None,"var(--against)")
a+=ga(182,52,246,52,"写す",214,44)
a+=gb(246,30,168,44,"文書の中の索引","保存される","var(--against)",True)
a+=ga(414,52,478,52)
a+=gb(478,30,150,44,"読み手")
a+='<text x="14" y="104" font-size="10.5" fill="var(--against)">同じ型の文書は、索引が全部同じ。文書について何も語らない</text>'
a+='<text x="14" y="150" font-size="11" fill="var(--infer)">変更後 ── 保存せず、取り出すときに両方から組み立てる</text>'
a+=gb(14,162,168,40,"型の読み方の指針",None,"var(--infer)")
a+=gb(14,210,168,40,"文書の中身",None,"var(--infer)")
a+=ga(182,182,240,204)
a+=ga(182,230,240,208)
a+=gb(246,184,168,44,"索引","その場で作る","var(--infer)",True)
a+=ga(414,206,478,206)
a+=gb(478,184,150,44,"読み手")
a+='<text x="14" y="272" font-size="10.5" fill="var(--infer)">保存しないので古くならない。文書ごとに違う</text>'
FIG=gsvg("0 0 646 288",a,
 "<b>いまの索引は、型の指針を写して保存している。</b>"
 "だから同じ型の文書はすべて同じ索引を持ち、その文書について何も語らない。")

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">どの鍵を引けばよいかが分かる<br><span class="sub">決め手</span></th>
<th>常に最新である</th><th>導いた値を文書に持たない</th><th>取り出しが速い</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">保存せず、取り出すときに毎回組み立てる<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}<br><span class="sub">1本読む</span></td></tr>
<tr><td class="cond">いまのまま置く</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">文書の中身から作って、保存する</td><td>{ok}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['どの鍵を引けばよいかが分かる<span class="keytag">決め手</span>',
      "索引の目的そのもの。全文を読まずに当たりを付け、必要な鍵だけ引くため",
      "<b>いまのまま</b> 型の読み方しか持たないので、"
      "<b>その文書のどこに何があるかが分からない</b>"]),
    ("",["常に最新である",
      "保存した値は、元が変わると古くなる。古い索引は、間違った鍵へ導く",
      "<b>いまのまま</b>／<b>作って保存する</b> ── どちらも写しなので古くなりうる"]),
    ("",["導いた値を文書に持たない",
      "承認済みの決定が「型の情報を実体へ写さない」と定めている。"
      "文書から導いた値も、持てば同じ問題を抱える",
      "<b>いまのまま</b>／<b>作って保存する</b> ── どちらも文書に持つ"]),
    ("",["取り出しが速い",
      "毎回作るなら、その文書を読む",
      "<b>毎回組み立てる（採る）</b> ── 1本読む。"
      "<b>ただし平均11KB・最大53KB で、AI が読む量は変わらない</b>"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "別々の文書（<code>uc-render-document</code> と <code>uc-check-scenario-drift</code>）の索引を比べたら、"
    "<b>共通する12ブロックとも中身が1文字も違わなかった</b>"),
  joint("だから"),
  step("conclude","言えること",
    "いまの索引は<b>その文書について何も語っていない</b>。"
    "中身は読み方の指針の写しで、同じ型ならすべて同じになる"),
  joint("目的に照らすと"),
  step("premise","前提",
    "索引の目的は、<b>どの鍵を引けば求めている情報が引けそうかが分かること</b>である。"
    "全文を読まずに当たりを付け、必要な鍵だけ引く"),
  joint("だから"),
  step("conclude","言えること",
    "<b>2つが要る。</b>「このブロックは何のために読むものか」（型から）と、"
    "「そこに何がどれだけあるか」（文書から）。"
    "<b>いまは前者しか持っていない</b>"),
  joint("持ち方も見た"),
  step("evidence","測った",
    "索引は <code>x-prompt-query</code> から作られて、実体（document.json）に保存されている。"
    "承認済みの決定は「<b>型の情報を実体へ写さない</b>」と定めている"),
  joint("作る手間を測ると"),
  step("evidence","測った",
    "文書は<b>253本・合計2.8MB・平均11KB・最大53KB</b>。"
    "毎回作っても<b>払うのはファイルの読み込みだけ</b>で、AI が読む量は変わらない"),
  joint("合わせると"),
  step("conclude","結論",
    "索引は保存しない。取り出すときに、型と文書の両方から毎回組み立てる"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（5件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["12ブロックとも同一",'<span class="kindtag unv">実測</span>',
      "2つの文書の索引を取り出して突き合わせた","—"]),
    ("keyrow",["索引の目的",'<span class="kindtag lim">利用者の言葉</span>',
      "「どの鍵で引けば求めている情報が引けそうかが分かるとよい」","—"]),
    ("",["型の情報を実体へ写さない",'<span class="kindtag unv">承認済みの決定</span>',
      "Schema を仕様から実装し、型は Document として置く","—"]),
    ("",["文書の大きさ",'<span class="kindtag unv">実測</span>',
      "253本・2.8MB・平均11KB・最大53KB",
      "<b>文書が桁違いに大きくなったとき</b>"]),
    ("",["AI が読む量は変わらない",'<span class="kindtag out">Waffle の設計</span>',
      "Waffle が読んで索引だけを返す","—"]),
  ]))

ret = tbl(["欄","例","何に効くか"],[
 ("keyrow",["<b>鍵</b>","<code>acceptanceCriteria</code>","<b>引くために要る</b>"]),
 ("keyrow",["<b>読む目的</b>","「何を満たせば正しいかを読みます」",
   "<b>求めている情報がここにありそうか</b>（型から）"]),
 ("",["見出し","受け入れ基準","同上"]),
 ("",["形","並び／文／組","要素を選べるか、丸ごとか"]),
 ("",["量","37件／1,240字","全部引くか、絞るか"]),
 ("keyrow",["<b>識別子</b>","並びなら、要素の名前を<b>全部</b>",
   "<b>どの要素を引くかを決められる</b>（文書から）"]),
 ("",["欄の名前","組なら、持っている欄","同上"]),
])

size = tbl(["","全文","索引","割合"],[
 ("",["<code>uc-render-document</code>","24,414字","3,116字","<b>12%</b>"]),
 ("",["<code>spec-implementation-abstraction</code>","6,368字","848字","<b>13%</b>"]),
])

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>索引を保存せず、取り出すときに毎回組み立てる</h1>'
 '<p class="lede">別々の文書の索引を比べたら、共通する12ブロックとも<b>1文字も違わなかった</b>。'
 'いまの索引は型の読み方の指針の写しで、<b>その文書について何も語っていない</b>。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>索引を文書に保存せず、取り出すときに毎回組み立てる</b>。'
  '組み立てる材料は<b>型と文書の両方</b>で、'
  '「このブロックは何のために読むものか」と「そこに何がどれだけあるか」を返す。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">索引の目的は、<b>どの鍵を引けば求めている情報が引けそうかが分かること</b>である。'
  'いまの索引は型の読み方しか持たないので、'
  '<b>その文書のどこに何があるかが分からない</b>。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>索引がどこから作られ、どこに住むか</b>である。",
  FIG +
  '<h3 class="sub-h">実際の索引 ── 同じ文書、同じ4ブロック</h3>'
  '<div class="cmp2">'
  f'<div class="pn"><span class="pl b">変更前 ── 型の指針だけ</span>'
  f'<div class="scroll"><pre>{e(before)}</pre></div></div>'
  f'<div class="pn"><span class="pl a">変更後 ── 型と文書の両方</span>'
  f'<div class="scroll"><pre>{e(after)}</pre></div></div></div>'
  '<p class="blob">変更前は<b>どの文書でも同じ</b>。変更後は'
  '<b>「受け入れ基準が37件あり、識別子はこれ」</b>まで分かるので、引く先を決められる。</p>'),

 sec("03","索引が返すもの",
   "7つの欄。<b>読む目的は型から、形・量・識別子は文書から</b>組み立てる。",
   ret +
   '<h3 class="sub-h">大きさ</h3>' + size +
   '<p class="blob">識別子を<b>全部</b>載せても、全文の12〜13%に収まる。'
   '先頭だけにすると8%になるが、<b>どれを引けばよいかが分からなくなる</b>ので、'
   '索引の役目を果たさない。</p>'),

 sec("04","判断を分けた軸",
   "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>取り出すたびに文書を1本読む</b>。",
   axis, axis_fold),

 sec("05","理由",
   "索引がその文書について何も語っていない。"
   "<b>目的に照らすと、型と文書の両方が要る。</b>",
   reason, reason_fold),

 sec("06","付随して決めたこと",
   "保存をやめると、いくつかの位置づけが決まる。3点を同時に決めた。",
   tbl(["論点","決定"],[
     ("keyrow",["<code>_index</code> という欄",
       "<b>schema から落とす。</b>保存しないので、宣言する必要がない"]),
     ("keyrow",["段1 の部品としての索引",
       "<b>表紙は増えない。</b>索引は保存される値ではなく、"
       "<b>値を取り出すことの一形態</b>"]),
     ("",["文のブロックに冒頭を載せるか",
       "<b>載せない。</b>冒頭のn文字は要約ではないので当たりの役に立つとは限らず、"
       "n を決めるという論点が増える。見出しで足りないなら、見出しのほうを直す"]),
   ]),
   fold("それぞれの根拠を開く（3件）",
     tbl(["論点","根拠"],[
       ("keyrow",["<code>_index</code> という欄",
         "いまは <code>readOnly</code> で「waffle が自動生成する。AI は直接書かない」と"
         "説明が付いている。<b>書き手が書かない欄を、書き手のための型に宣言している</b>"]),
       ("keyrow",["段1 の部品としての索引",
         "保存するなら表紙に項目が1つ増える。保存しないなら増えない。"
         "<b>索引は取り出し方であって、文書が持つものではない</b>"]),
       ("",["文のブロックに冒頭を載せるか",
         "冒頭は書き出しであって要約ではない。"
         "<b>載せても当たりが正確になるとは限らない</b>のに、n という決めどころが増える"]),
     ]))),

 sec("07","答えないこと",
   "2つ残る。<b>どちらも、この決定が成り立たなくなったときに考える</b>ものである。",
   tbl(["項目","何が決まっていないか","いつ決めるか"],[
     ("",["取り出しが遅くなったときの手当て",
       "写しを持つか、別の場所へ置くか",
       "<b>実際に遅いと分かったとき。</b>いまは平均11KB で問題にならない"]),
     ("",["索引を横断して引けるようにするか",
       "複数の文書の索引をまとめて見る道",
       "<b>横断の取り出しを見直すとき</b>"]),
   ])),

 '<section><h2><span class="num">08</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span></div></section>',

 sec("09","関連","この決定は、段1 の部品を確定させるための入力になる。","",
  fold("縛る対象と、前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","索引の作り方と住みか"]),
      ("keyrow",["先立つ決定","Schema を仕様から実装し、型は Document として置く（承認済み）── "
        "<b>型の情報を実体へ写さない、がここで決まっている</b>"]),
      ("",["書き直す文書",
        "<code>uc-query-document</code>（索引の取り出し）／型11本（<code>_index</code> を落とす）"]),
      ("",["この決定を使う予定",
        "段1 の部品を確定させる。<b>索引が保存されないので、表紙は増えない</b>"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
.cmp2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:52rem){.cmp2{grid-template-columns:1fr}}
.cmp2 .pn{display:flex;flex-direction:column;gap:.4rem;min-width:0}
.cmp2 .pl{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em}
.cmp2 .pl.b{color:var(--against)} .cmp2 .pl.a{color:var(--infer)}
.cmp2 pre{margin:0;padding:.8rem .95rem;font-family:var(--mono);font-size:.72rem;
          line-height:1.75;white-space:pre;color:var(--ink-soft)}
"""
html_out=("<title>索引を保存せず、取り出すときに毎回組み立てる</title>"
      f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-index-on-read.html").write_text(html_out,encoding="utf-8")
print("書いた",len(html_out))

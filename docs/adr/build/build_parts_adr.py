import sys, json, pathlib, html
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
e=html.escape
R=lambda n: pathlib.Path(f"{S}/{n}").read_text(encoding="utf-8")
wide=R("idx_wide.json"); nerr=R("idx_narrow_err.json")

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
def gsvg(vb,inner,cap):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

a=''
a+='<text x="14" y="18" font-size="11" fill="var(--against)">変更前 ── 要素の欄の名前が型ごとに違い、実装が説明を当てる</text>'
a+=gb(14,30,150,40,"term / definition",None,"var(--against)")
a+=gb(14,78,150,40,"conceptId / note",None,"var(--against)")
a+=gb(14,126,150,40,"name / problem",None,"var(--against)")
a+=ga(164,50,236,88); a+=ga(164,98,236,98); a+=ga(164,146,236,108)
a+=gb(236,78,180,40,"実装が欄名を当てる",None,"var(--against)",True)
a+=ga(416,98,488,98)
a+=gb(488,78,190,40,"半分が落ちる","281件中152件","var(--against)")
a+='<text x="14" y="200" font-size="11" fill="var(--infer)">変更後 ── 並びの部品が、要素に鍵と説明を持たせる</text>'
a+=gb(14,212,150,44,"並びの部品","段1 が提供","var(--infer)",True)
a+=ga(164,234,236,234)
a+=gb(236,212,180,44,"要素は鍵と説明を持つ","構造で決まっている","var(--infer)")
a+=ga(416,234,488,234)
a+=gb(488,212,190,44,"索引が必ず作れる","当てる必要が無い","var(--infer)")
FIG1=gsvg("0 0 700 272",a,
 "<b>形は既に揃っていて、名前だけが型ごとに違っていた。</b>"
 "名前を宣言させるとばらつきを追認することになり、宣言し忘れは黙って落ちる。")

b=''
b+=gb(14,34,140,44,"読み手",None)
b+=ga(154,56,220,56)
b+=gb(220,34,190,44,"1段目の索引","鍵と読み方・全文の4%","var(--infer)",True)
b+=ga(410,56,476,56)
b+=gb(476,34,180,44,"引くブロックを決める")
b+=ga(566,78,566,118)
b+=gb(424,118,232,44,"2段目の索引","そのブロックの鍵と説明","var(--infer)",True)
b+=ga(424,140,290,140)
b+=gb(100,118,190,44,"その要素だけを引く")
FIG2=gsvg("0 0 690 180",b,
 "<b>2段に分けると、切り詰める長さを決めなくてよくなる。</b>"
 "当たりを付けて1ブロック取っても、全文の7%で済む。")

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">宣言し忘れが起こりようがない<br><span class="sub">決め手</span></th>
<th>索引が必ず作れる</th><th>段2 に負担をかけない</th><th>いまの型を書き換えずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">部品が鍵と説明を持つ<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">どの欄が鍵か説明かを宣言させる</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">いまのまま、実装が欄名を当てる</td><td>{ng}</td><td>{ng}</td><td>{ok}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['宣言し忘れが起こりようがない<span class="keytag">決め手</span>',
      "落ちても誰も気づかない。索引は出るが説明が空になるだけで、"
      "<b>間違った鍵へ導く</b>",
      "<b>宣言させる</b> 書き忘れれば落ちる<br>"
      "<b>いまのまま</b> 実装の一覧に無い名前は黙って落ちる。"
      "実測で<b>281件中152件が落ちた</b>"]),
    ("",["索引が必ず作れる",
      "作れない要素が混じると、その部分だけ当たりを付けられない",
      "<b>宣言させる</b>／<b>いまのまま</b> ── どちらも作れない要素が出る"]),
    ("",["段2 に負担をかけない",
      "段2 は組み合わせるだけであるべき。毎回2つ宣言させるのは、部品の不足を書き手へ押し付けること",
      "<b>宣言させる</b> 要素の形ごとに宣言が要る"]),
    ("",["いまの型を書き換えずに済む",
      "書き換える範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>部品が持つ（採る）</b> 137のブロックのうち、"
      "要素の欄の名前を揃える必要があるものを書き換える"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("premise","前提",
    "索引の目的は、<b>どの鍵を引けば求めている情報が引けそうかが分かること</b>である"),
  joint("だから"),
  step("conclude","言えること",
    "索引は、要素ごとに<b>鍵と説明が対</b>になっていなければ役に立たない。"
    "鍵だけでは何の要素か分からず、説明だけでは引けない"),
  joint("いまどう作られているかを見た"),
  step("evidence","測った",
    "実装が<b>欄の名前の一覧を持っていて、最初に見つかったものを説明として使っている</b>。"
    "宣言から導いていない"),
  joint("当たり具合を測ると"),
  step("evidence","測った",
    "組の要素281件のうち、<b>説明が取れたのは129件（46%）、取れなかったのが152件（54%）</b>。"
    "鍵が取れなかったのは118件"),
  joint("落ちたものを見ると"),
  step("evidence","測った",
    "<code>term</code>/<code>definition</code> が89件、<code>conceptId</code>/<code>note</code>、"
    "<code>name</code>/<code>problem</code>、<code>name</code>/<code>summary</code>。"
    "<b>どれも鍵と説明の対になっている。形は揃っていて、名前だけが型ごとに違う</b>"),
  joint("だから"),
  step("conclude","言えること",
    "名前を宣言させるのは<b>ばらつきを追認する</b>ことになる。"
    "しかも宣言し忘れは黙って落ちる ── いま <code>definition</code> で起きているのがそれである"),
  joint("結論"),
  step("conclude","結論",
    "<b>部品の側が、要素に鍵と説明を持たせる。</b>"
    "そうすれば索引は部品の性質から必ず導け、宣言も推測も要らない"),
  joint("なお"),
  step("premise","前提",
    "図は既にそうなっている。<b><code>asserts</code>（何を主張するか）と "
    "<code>reading</code>（どう読むか）が、鍵と説明にあたる</b>。"
    "読み方を必須にしたのは、同じ考えである"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["281件中152件で説明が取れない",'<span class="kindtag unv">実測</span>',
      "24本の文書の、組の要素すべてに当てた","—"]),
    ("keyrow",["落ちたものも鍵と説明の対",'<span class="kindtag unv">実測</span>',
      "落ちた要素が持っていた文字列の欄を数えた",
      "<b>鍵も説明も持たない要素が出てきたとき</b>"]),
    ("",["索引の目的",'<span class="kindtag lim">利用者の言葉</span>',
      "「どの鍵で引けば求めている情報が引けそうかが分かるとよい」","—"]),
    ("",["図は既にそうなっている",'<span class="kindtag unv">承認済みの決定</span>',
      "図の宣言を、主張を軸にした形へ置き換える","—"]),
  ]))

parts = tbl(["部品","鍵にあたるもの","説明にあたるもの"],[
 ("keyrow",["<b>並び</b>","要素の鍵","要素の説明"]),
 ("",["<b>まとまり</b>","欄の名前","欄の値"]),
 ("",["<b>入れ子の木</b>","節の名前","節の要約"]),
 ("keyrow",["<b>図</b>","<code>asserts</code>（何を主張するか）",
   "<code>reading</code>（どう読むか）<span class='sub'>既にそうなっている</span>"]),
 ("",["<b>ブロック</b>","ブロックの鍵","読み方（型から）"]),
])

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>部品に鍵と説明を持たせ、索引を取り出すときに組み立てる</h1>'
 '<p class="lede">索引を作るのに、実装が欄の名前を当てていた。'
 '<b>組の要素281件のうち152件で説明が取れなかった。</b>'
 '落ちたものも鍵と説明の対を持っていて、<b>名前だけが型ごとに違っていた</b>。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>段1 が提供する部品に、鍵と説明を持たせる</b>。'
  'そして<b>索引を文書に保存せず、取り出すときに2段で組み立てる</b> ── '
  '広く取るときは鍵と読み方、細かく取るときはそのブロックの鍵と説明。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt"><b>どの欄が鍵か説明かを宣言させると、宣言し忘れが黙って落ちる。</b>'
  '部品の側が持てば、落ちようがない。'
  '形は既に揃っていて、名前だけが型ごとに違っていた。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>鍵と説明が、どこで保証されるか</b>である。",
  FIG1 + '<h3 class="sub-h">どの部品でも、鍵と説明が対になる</h3>' + parts),

 sec("03","索引は2段になる",
  "部品が鍵と説明を持てば、索引は部品の性質から導ける。"
  "<b>2段に分けると、切り詰める長さを決めなくてよくなる。</b>",
  FIG2 +
  '<h3 class="sub-h">大きさ ── <code>uc-render-document</code>（全文24,414字）</h3>' +
  tbl(["取り出し","大きさ","全文に対して"],[
    ("keyrow",["1段目（12ブロックの鍵と読み方）","1,213字","<b>4%</b>"]),
    ("",["2段目 ── 誤り（6件）","645字","2%"]),
    ("",["2段目 ── 受け入れ基準（37件）","5,543字","22%"]),
    ("keyrow",["<b>1段目＋1ブロック</b>","1,858字","<b>7%</b>"]),
  ]) +
  '<h3 class="sub-h">実物 ── 1段目</h3>'
  f'<div class="scroll"><pre class="out">{e(wide)}</pre></div>'
  '<h3 class="sub-h">実物 ── 2段目（誤り）</h3>'
  f'<div class="scroll"><pre class="out">{e(nerr)}</pre></div>'),

 sec("04","理由",
  "索引には鍵と説明の対が要る。"
  "<b>いまは実装が名前を当てていて、半分以上が落ちている。</b>",
  reason, reason_fold),

 sec("05","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>いまの型を書き換えることになる</b>。",
  axis, axis_fold),

 sec("06","付随して決めたこと",
  "部品が鍵と説明を持つと、索引の持ち方と欄が決まる。4点を同時に決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["索引を保存するか",
      "<b>しない。</b>取り出すときに、型と文書の両方から毎回組み立てる。"
      "文書は平均11KB なので、<b>AI が読む量は変わらない</b>"]),
    ("keyrow",["<code>_index</code> という欄",
      "<b>schema から落とす。</b>保存しないので宣言する必要がない"]),
    ("",["索引が返す欄",
      "<b>1段目は鍵と読み方。2段目は鍵と説明。</b>"
      "形・量・見出し・欄の名前は落とす ── 鍵と説明から導けるか、読み方と重なる"]),
    ("",["段1 の部品としての索引",
      "<b>表紙は増えない。</b>索引は保存される値ではなく、値を取り出すことの一形態"]),
  ]),
  fold("それぞれの根拠を開く（4件）",
    tbl(["論点","根拠"],[
      ("keyrow",["索引を保存するか",
        "保存した値は元が変わると古くなる。<b>古い索引は間違った鍵へ導く</b>。"
        "いまの索引がまさにその形で、型の指針を写して保存している"]),
      ("",["<code>_index</code> という欄",
        "いまは <code>readOnly</code> で「waffle が自動生成する。AI は直接書かない」と付いている。"
        "<b>書き手が書かない欄を、書き手のための型に宣言している</b>"]),
      ("keyrow",["索引が返す欄",
        "<b>形</b>は識別子が並んでいれば分かる。<b>量</b>は要素の数がそのまま。"
        "<b>見出し</b>は読み方と重なる。<b>欄の名前</b>は要素の鍵に含まれる"]),
      ("",["段1 の部品としての索引",
        "保存するなら表紙に項目が増える。保存しないなら増えない"]),
    ]))),

 sec("07","答えないこと",
  "3つ残る。<b>いずれも使ってみないと決められない</b>。",
  tbl(["項目","何が決まっていないか","いつ決めるか"],[
    ("",["1段目に量を戻すか",
      "「37件ある」が分かると、2段目を引くかの判断が変わるかもしれない",
      "<b>使ってみて要るなら戻す</b>"]),
    ("",["2段目をブロック単位より細かくできるか",
      "37件のうち一部だけを引く道があるか","同上"]),
    ("keyrow",["いまの型をどう書き換えるか",
      "要素の欄の名前を揃える対象と順序",
      "<b>移す計画で決める。</b>この決定は形だけを定める"]),
  ])),

 '<section><h2><span class="num">08</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-16</span></div></section>',

 sec("09","関連","この決定は、段1 の部品を確定させる土台になる。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","段1 が提供する部品の性質と、索引の作り方"]),
      ("keyrow",["先立つ決定","Schema を仕様から実装し、型は Document として置く（承認済み）── "
        "<b>型の情報を実体へ写さない、がここで決まっている</b>"]),
      ("",["先立つ決定","語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける（承認済み）"]),
      ("",["先立つ決定","図の宣言を、主張を軸にした形へ置き換える（承認済み）── "
        "<b>図は既に鍵と説明を持っている</b>"]),
      ("",["書き直す文書",
        "<code>uc-query-document</code>（索引の取り出し）／型10本（<code>_index</code> を落とし、要素の欄の名前を揃える）"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
pre.out{margin:0;padding:.9rem 1rem;font-family:var(--mono);font-size:.73rem;
        line-height:1.75;white-space:pre;color:var(--ink-soft)}
"""
out=("<title>部品に鍵と説明を持たせ、索引を取り出すときに組み立てる</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-parts-key-and-gloss.html").write_text(out,encoding="utf-8")
print("書いた",len(out))

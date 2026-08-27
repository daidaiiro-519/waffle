import sys, json, pathlib, html
S="/home/daidaiiro/workspace/waffle/docs/adr/build"
sys.path.insert(0,S)
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
e=html.escape; C=lambda s: f"<code>{s}</code>"
before=pathlib.Path(S+"/meta_before.json").read_text(encoding="utf-8")
after=pathlib.Path(S+"/meta_after.json").read_text(encoding="utf-8")

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="12.5" font-weight="600" fill="var(--ink)">{t}</text>'
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
a+='<text x="14" y="18" font-size="11" fill="var(--against)">変更前 ── ひとつの欄に、2系統の状態が入っている</text>'
a+=gb(14,32,130,40,"作成済",None,"var(--against)")
a+=ga(144,52,182,52); a+=gb(182,32,130,40,"検証済",None,"var(--against)")
a+=ga(312,52,350,52); a+=gb(350,32,130,40,"描画済",None,"var(--against)")
a+=ga(480,52,518,52); a+=gb(518,32,130,40,"終端",None,"var(--against)")
a+=gb(14,84,130,40,"下書き",None,"var(--against)")
a+=ga(144,104,182,104); a+=gb(182,84,130,40,"有効",None,"var(--against)")
a+=ga(312,104,350,104); a+=gb(350,84,130,40,"非推奨",None,"var(--against)")
a+='<text x="668" y="56" font-size="10.5" fill="var(--against)">工程の系統（2本の型）</text>'
a+='<text x="500" y="108" font-size="10.5" fill="var(--against)">成熟の系統（6本の型）</text>'
a+='<text x="14" y="160" font-size="11" fill="var(--infer)">変更後 ── 導けないものだけが残る</text>'
a+=gb(14,174,130,44,"下書き",None,"var(--infer)",True)
a+=ga(144,196,182,196); a+=gb(182,174,130,44,"有効",None,"var(--infer)",True)
a+='<text x="350" y="200" font-size="10.5" fill="var(--infer)">これに頼ってよいか ── 人が決める</text>'
FIG1=gsvg("0 0 800 240",a,
 "<b>ひとつの欄に、性質の違う2系統が入っていた。</b>"
 "工程は導ける事実なので落とし、<b>導けないものだけが状態として残る</b>。")

b=''
b+='<text x="14" y="18" font-size="11" fill="var(--against)">変更前 ── 保存された札を見て、描いてよいかを決める</text>'
b+=gb(14,32,150,44,"描く",None,"var(--against)")
b+=ga(164,54,226,54)
b+=gb(226,32,180,44,"状態は検証済か","保存された札","var(--against)",True)
b+=ga(406,54,468,54)
b+=gb(468,32,150,44,"描いてよい")
b+='<text x="14" y="98" font-size="10.5" fill="var(--against)">値を埋めても札は戻らないので、札が嘘をつきうる</text>'
b+='<text x="14" y="144" font-size="11" fill="var(--infer)">変更後 ── その場で判定する</text>'
b+=gb(14,158,150,44,"描く",None,"var(--infer)")
b+=ga(164,180,226,180)
b+=gb(226,158,180,44,"逸脱していないか","型を引数で受け取る","var(--infer)",True)
b+=ga(406,180,468,180)
b+=gb(468,158,150,44,"描いてよい")
b+='<text x="14" y="224" font-size="10.5" fill="var(--infer)">保存しないので古くならない。順序ではなく、条件になる</text>'
FIG2=gsvg("0 0 640 240",b,
 "<b>「検証前に描かせない」は、状態の遷移ではなく、描くコマンドの事前条件になる。</b>"
 "確かめる相手が札から、その場の判定へ変わる。")

derive = tbl(["問い","導けるか","どこから導けるか"],[
 ("",["適合しているか","<b>導ける</b>",f"{C('schemaRef')} を解決して、逸脱していないかを判定する"]),
 ("",["描いたか","<b>導ける</b>","決まった場所に成果物があるかを見る"]),
 ("",["中身に何があるか","<b>導ける</b>","文書と型から索引を組み立てる（承認済み）"]),
 ("keyrow",["<b>これに頼ってよいか</b>","<b>導けない</b>",
   "<b>人が下す判断。文書のどこにも書かれていない</b>"]),
])

holds = tbl(["Document が持つもの","中身","なぜ持つか"],[
 ("keyrow",["<b>表紙</b>","識別子／型と版／種別／役どころ／時刻／ラベル","<b>導けない。</b>Document がエンティティである以上、同一性と出自が要る"]),
 ("keyrow",["<b>使ってよいか</b>","下書き／有効","<b>導けない。</b>人が下す判断"]),
 ("",["~~非推奨~~","~~もう頼るなという札~~","<b>持たない。</b>誰も守っておらず、参照されても何も起きない。実物3本・<b>参照0件</b>"]),
 ("keyrow",["<b>content</b>","型を知らない木。値は外から渡される","<b>文書の中身そのもの</b>"]),
 ("",["~~工程の状態~~","~~作成済／検証済／描画済／終端~~","<b>導けるので持たない</b>"]),
 ("",["~~索引~~","~~ブロックごとの読み方~~","<b>導けるので持たない</b>（承認済み）"]),
])

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">導いた値を文書に持たない<br><span class="sub">決め手</span></th>
<th>札が古くならない</th><th>同じ表を複製しない</th><th>いまの文書を書き換えずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">導けないものだけを持つ<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">2系統を認め、段1 が両方の遷移表を持つ</td><td>{ng}</td><td>{ng}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">いまのまま置く</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['導いた値を文書に持たない<span class="keytag">決め手</span>',
      "<b>承認済みの決定が定めている。</b>保存すれば古くなり、古い札は嘘をつく",
      "<b>2系統を認める</b>／<b>いまのまま</b> ── どちらも工程の状態を保存する"]),
    ("",["札が古くならない",
      "古い札は、間違った判断へ導く",
      f"<b>2系統を認める</b>／<b>いまのまま</b> ── {C('fill')} は状態に触れないので、"
      "<b>検証済のまま値を書き換えられる</b>"]),
    ("",["同じ表を複製しない",
      "正本が複数あると、片方だけ直したときに食い違う",
      "<b>いまのまま</b> 同じ遷移表が2本の型に書かれ、1行も違わない"]),
    ("",["いまの文書を書き換えずに済む",
      "書き換える範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>導けないものだけを持つ（採る）</b>／<b>2系統を認める</b> ── どちらも書き換える"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("premise","前提",
    "承認済みの決定が<b>「導いた値を文書に持たない」</b>と定めている。"
    "索引を保存しないと決めたときの、軸の条件のひとつである"),
  joint("Document に当てて問い直すと"),
  step("premise","前提",
    "<b>文書と、その型と、成果物から導けないものは何か。</b>"
    "導けるものは、必要なときに求めればよい"),
  joint("4つを当てた"),
  step("conclude","言えること",
    "適合したか・描いたか・中身に何があるかは<b>すべて導ける</b>。"
    "導けないのは<b>「これに頼ってよいか」の1つだけ</b>である"),
  joint("だから"),
  step("conclude","言えること",
    "<b>工程の状態は持たない。</b>"
    "Document が持つのは、表紙と content と「使ってよいか」だけになる"),
  joint("守っていたものはどうなるか"),
  step("conclude","結論",
    "「検証前に描かせない」は<b>状態の遷移ではなく、描くコマンドの事前条件</b>になる。"
    "型を引数で受け取り、その場で判定する ── "
    "<b>順序ではなく、条件である</b>"),
  joint("裏づけを取った"),
  step("evidence","測った",
    f"{C('fill')} は <code>status</code> に一切触れない。"
    "<b>検証済のまま値を書き換えられる</b> ── 札が嘘をつきうる状態が、実際に作れる"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["導いた値を文書に持たない",'<span class="kindtag unv">承認済みの決定</span>',
      "部品に鍵と説明を持たせ、索引を取り出すときに組み立てる","—"]),
    ("keyrow",["適合はいつでも判定できる",'<span class="kindtag unv">承認済みの決定</span>',
      f"Schema は3つの操作を持つ ── Document は {C('schemaRef')} を持ち、"
      "逸脱していないかを型を引数に判定する","—"]),
    ("",["描いたかは成果物を見れば分かる",'<span class="kindtag unv">承認済みの決定</span>',
      "描くことと、配ることを分ける ── 成果物は決まった場所に置かれる",
      "<b>成果物の場所が決まらなくなったとき</b>"]),
    ("",["札が嘘をつきうる",'<span class="kindtag unv">実測</span>',
      f"{C('fill')} の実装が <code>status</code> に触れないこと","—"]),
  ]))

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>Document は、導けないものだけを持つ</h1>'
 '<p class="lede">ひとつの <code>status</code> に、性質の違う2系統が入っていた ── '
 '<b>工程</b>（作成済／検証済／描画済）と<b>成熟</b>（下書き／有効／非推奨）。'
 '工程は<b>導ける事実</b>なので、保存すれば古くなる。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle において、'
  '<b>Document が持つのは、表紙と content と「使ってよいか」だけ</b>とする。'
  '工程の状態（作成済／検証済／描画済）は持たない。'
  '<b>「検証前に描かせない」は、状態の遷移ではなく、描くコマンドの事前条件とする。</b></p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt"><b>文書と、その型と、成果物から導けないものだけを持つ。</b>'
  '導けるものを保存すれば古くなる ── '
  f'いま {C("fill")} は <code>status</code> に触れないので、'
  '<b>検証済のまま値を書き換えられる</b>。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>何を保存し、何をその場で求めるか</b>である。",
  FIG1 +
  '<h3 class="sub-h">実物の表紙 ── 同じ欄に、違う系統の値が入っている</h3>'
  '<div class="cmp2">'
  f'<div class="pn"><span class="pl b">変更前</span>'
  f'<div class="scroll"><pre>{e(before)}</pre></div></div>'
  f'<div class="pn"><span class="pl a">変更後</span>'
  f'<div class="scroll"><pre>{e(after)}</pre></div></div></div>'
  '<p class="blob">同じ <code>status</code> という欄に、'
  '<b>片方は「検証済」、もう片方は「有効」</b>が入っている。'
  '<b>問うていることが違う。</b></p>'),

 sec("03","検証前に描かせない、はどうなるか",
  "<b>順序ではなく、条件になる。</b>確かめる相手が、保存された札からその場の判定へ変わる。",
  FIG2),

 sec("04","導けるか、導けないか",
  "4つを当てると、<b>導けないのは1つだけ</b>である。",
  derive +
  '<h3 class="sub-h">Document が持つもの</h3>' + holds),

 sec("05","理由",
  "承認済みの決定が「導いた値を文書に持たない」と定めている。"
  "<b>Document に当てて問い直すと、残るのは1つだけになる。</b>",
  reason, reason_fold),

 sec("06","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>いまの文書を書き換えることになる</b>。",
  axis, axis_fold),

 sec("07","付随して決めたこと",
  "状態が減ると、いくつかの持ち物と仕掛けが決まる。3点を同時に決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["遷移表",
      "<b>持たない。</b>工程が消えるので要らなくなる。"
      "成熟は一方向の並びなので、表を書くほどのものではない"]),
    ("keyrow",["content の持ち方",
      "<b>型を知らない木として持つ。</b>値は外から渡され、Document は置くだけ。"
      "型に沿っているかは、型を引数に受け取ったときだけ分かる"]),
    ("",["それでも正しさは正せる",
      f"Document は {C('schemaRef')} を持つので、<b>いつでも判定できる</b>。"
      "「content は型に適合する」は不変条件のまま ── "
      "<b>守り方が「引数で受け取って判定する」形になるだけ</b>"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("keyrow",["遷移表",
        "同じ遷移表が2本の型に書かれ、<b>1行も違わない</b>。"
        "工程を落とせば、複製ごと消える"]),
      ("keyrow",["content の持ち方",
        "<b>型を知った構造として持つと、エンティティが型に依存する。</b>"
        "承認済みの「参照は持つが自分では解決しない」が崩れる"]),
      ("",["それでも正しさは正せる",
        f"{C('schemaRef')} が常に在るという不変条件が、"
        "<b>正しさを確かめられることを保証している</b>。"
        "参照が欠けたら、正しさを問うことすらできなくなる"]),
    ]))),

 sec("08","答えないこと",
  "<b>2つは閉じた。</b>残るのは1つで、移す計画で決める。",
  tbl(["項目","何が決まっていないか","いつ決めるか"],[
    ("keyrow",["<b>「使ってよいか」の語</b>",
      "<b>下書き／有効の2つに決めた。</b>非推奨は落とす ── 誰も守っておらず、実物3本の参照は0件だった。<b>退役は文書を消すことで表す</b>","<b>決着（2026-08-16）</b>"]),
    ("keyrow",["<b>終端化する操作</b>",
      "<b>要らない。</b>非推奨へ落とす操作だったので、行き先ごと無くなる。<b>Document のコマンドは4つになる</b>","<b>決着（2026-08-16）</b>"]),
    ("keyrow",["いまの文書をどう書き換えるか",
      f"<b>253本</b>の <code>status</code> をどう移すか。"
      "工程の値を持つものは、何に置き換わるか","<b>移す計画</b>"]),
  ])),

 '<section><h2><span class="num">09</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-16 承認。同日、非推奨と終端化するを削った（決定の中身は変えていない）</span></div></section>',

 sec("10","関連","この決定で、段1・段2・Document の三方が揃う。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","Document が持つものと、状態の意味"]),
      ("keyrow",["<b>完成イメージ</b>","<b><a href=\"https://claude.ai/code/artifact/df54f985-bf86-4931-b0be-de128ee32978\">Document は何を持ち、どう呼ばれるか</a></b> ── 持ち物／操作の入出力／型の解決／併用の要否"]),
      ("keyrow",["先立つ決定","部品に鍵と説明を持たせ、索引を取り出すときに組み立てる（承認済み）── "
        "<b>導いた値を文書に持たない、がここで決まっている</b>"]),
      ("",["先立つ決定","Schema は3つの操作を持つ（承認済み）── Document の5つと参照の規律"]),
      ("",["先立つ決定","描くことと、配ることを分ける（承認済み）"]),
      ("",["書き直す文書",
        f"{C('agg-document')}（書き直し）／型10本（<code>status</code> と "
        f"<code>x-lifecycle</code>）／{C('uc-render-document')}・{C('uc-validate-document')}"]),
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
out=("<title>Document は、導けないものだけを持つ</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-document-holds.html").write_text(out,encoding="utf-8")
print("書いた",len(out))

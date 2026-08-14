import json, pathlib
S = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
CSS   = S.joinpath("newfmt.css").read_text(encoding="utf-8")
TOK   = S.joinpath("fig_tokens.txt").read_text(encoding="utf-8")
FIG   = json.loads(S.joinpath("layer_figs.json").read_text(encoding="utf-8"))

def sec(n, t, lead, main, fold=None):
    h = f'<section><h2><span class="num">{n}</span>{t}</h2>'
    if lead: h += f'<p class="lead">{lead}</p>'
    h += main
    if fold: h += fold
    return h + "</section>"

def fold(summary, inner):
    return f'<details class="fold"><summary>{summary}</summary>{inner}</details>'

def tbl(head, rows, cls=""):
    hh = "".join(f"<th>{c}</th>" for c in head)
    bb = "".join(f'<tr class="{r[0]}">' + "".join(f'<td class="cond">{c}</td>' if i==0 else f"<td>{c}</td>"
         for i, c in enumerate(r[1])) + "</tr>" for r in rows)
    return f'<div class="scroll{cls}"><table><thead><tr>{hh}</tr></thead><tbody>{bb}</tbody></table></div>'

ok  = '<span class="mk ok"><span class="sym">○</span></span>'
ng  = '<span class="mk ng"><span class="sym">×</span></span>'

axis_main = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">向きを偽らない<br><span class="sub">決め手</span></th>
<th>層を増やさない</th><th>仕様が動かない</th><th>1本の線で読める</th><th>読み順が通る</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">2つの経路にする<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td><td>{ng}</td></tr>
<tr><td class="cond">仕様の上に積む</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td><td>{ok}</td></tr>
<tr><td class="cond">仕様と実装の間に挟む</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（5件）",
  tbl(["条件（全文）", "なぜこの条件が要るか", "× の理由"], [
    ("keyrow", ['依存の向きを偽らない<span class="keytag">決め手</span>',
      "宣言された関係と実際の依存が食い違うと、どちらが正かを人が決めない限り検知できない。食い違ったまま誰も気づかない状態が現に起きている",
      "<b>代案</b> 仕様が規約から導かれると読め、実際の依存と逆になる"]),
    ("", ["層を増やさない",
      "層が増えるほど、何をどこへ置くかの判断が毎回増える。対称性のために層を作ると、実装の綴りが仕様へ入る口ができる",
      "<b>代案</b> 層を1つ足す"]),
    ("", ["規約を変えても仕様が動かない",
      "製品ごとの綴りの違いが仕様へ波及すると、仕様が製品固有になり、他へ持ち出せなくなる",
      "<b>代案</b> 規約が仕様の上または途中にあるので、改訂が波及すると読める"]),
    ("", ["図が1本の線で読める", "関係を人へ説明するとき、分岐があるほど読み手の負担が増える",
      "<b>採る案</b> 分岐と合流があり、2本を追う必要がある"]),
    ("", ["上から下へ読み順が通る", "上から順に追うだけで関係が分かる形なら、説明が要らない",
      "<b>採る案</b> 2本を並行に読む必要がある"]),
  ]))

def step(kind, lbl, txt):
    return f'<div class="step {kind}"><span class="lbl">{lbl}</span><span class="txt">{txt}</span></div>'
def joint(t): return f'<div class="joint">{t}</div>'

reason_main = '<div class="chain">' + "".join([
  step("evidence","測った","仕様の文書のうち、規約を名指ししているのは3件だけ。いずれも規約そのものを入力に取るユースケースだった"),
  joint("だから"),
  step("conclude","言えること","仕様の執筆は規約に依存していない"),
  joint("一方で"),
  step("evidence","測った","実装とテストの置き場所・命名・単位・依存は、すべて規約の宣言から導出されている"),
  joint("ここで置いた前提"),
  step("premise","確かめていない","今後も、仕様の執筆に規約が要る場面は現れない"),
  joint("合わせると"),
  step("conclude","結論","規約が効くのは実装とテストを導くところだけ。上下に積むと依存の向きを偽ることになる"),
  joint("ただし"),
  step("counter","反証","「規約を扱うユースケースだから例外」は私が付けた解釈であって、観測ではない"),
]) + "</div>"

reason_fold = fold("段の出所と、崩れるときを開く（4件）",
  tbl(["段", "出所", "崩れるとき"], [
    ("", ["仕様のうち規約を名指しは3件", "仕様の走査と、各文書の入力欄の確認", "規約を入力に取らない仕様が、規約を参照し始めたとき"]),
    ("", ["置き場所・命名は規約から導出", "ドリフト検知が規約の識別子を起点に動く", "導出せず、対応を保存する検知が増えたとき"]),
    ("", ["今後も規約は要らない（前提）", "—", "製品ごとに仕様の書き方を変える必要が出たとき"]),
    ("", ["仕様は規約に依存しない（推論）",
      '拠り所 knowledge「仕様の語彙にパターン名を入れない ── 使えるのは規約から下だけ」', "—"]),
  ]))

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>規約は層ではなく、実装を導くもう一つの入力とする</h1>'
 '<p class="lede">仕様・規約・実装の関係を、一直線の積み重ねから、knowledge だけを共通の出発点とする2つの経路へ改める。</p></header>',

 sec("01","決定", None,
   '<div class="decision"><p class="main">規約は仕様の層ではない。仕様と規約は同じ格で、'
   'knowledge だけを共通の出発点とし、実装とテストで合流する2つの経路である。</p>'
   '<div class="key"><span class="lbl">決め手</span>'
   '<span class="txt">仕様の執筆は規約を読んでいない。上に積むと'
   '<b>「仕様は規約から導かれる」と読め、実際の依存と食い違う</b>。</span></div></div>'),

 sec("02","変更前と変更後", "規約が仕様の上から外れ、実装とテストの手前で合流する位置へ動く。",
   '<div class="cmp stack">'
   f'<div class="pane"><span class="pane-label b">変更前</span><div class="box">{FIG["before"]}</div></div>'
   f'<div class="pane"><span class="pane-label a">変更後</span><div class="box">{FIG["after"]}</div></div>'
   '</div>'),

 sec("03","理由", None, reason_main, reason_fold),

 sec("04","判断を分けた軸",
   "採る案は、依存の向きを偽らないという条件を満たす唯一の案。読みやすさ2つを落として、それを取った。",
   axis_main, axis_fold),

 sec("05","付随して決めたこと", "対称性のために層を作らない、が4件を貫く。",
   tbl(["論点", "決定"], [
     ("", ["schema と仕様の間に規約を置くか", "置かない。その位置に相当するのは CodingSchema"]),
     ("", ["仕様を書くとき規約を読むか", "読まない。読むのは schema の記入指示と knowledge だけ"]),
     ("", ["実装を導く入力", "仕様と規約の両方。どちらか一方では具体が決まらない"]),
     ("", ["どこまでを文書にするか", "上は knowledge、下は実装とテスト"]),
   ]),
   fold("それぞれの根拠を開く（4件）",
     tbl(["論点", "根拠"], [
       ("", ["schema と仕様の間", "対称性のために層を作ると、「仕様の綴り方」という名で実装の綴りが仕様へ入る口ができる"]),
       ("", ["規約を読むか", "読ませると、この製品ではこう綴るという話が仕様へ流れ込む"]),
       ("", ["実装を導く入力", "仕様だけで実装が決まる形にすると、仕様が実装の転記になる"]),
       ("", ["どこまでを文書にするか", "抽象の段は上にも下にも無限に作れるので、どこで切るかを決めないと際限がなくなる"]),
     ]))),

 sec("06","答えないこと", "分け目と綴りは別の決定へ。将来のことは行き先を持たない。",
   tbl(["項目", "種別", "行き先"], [
     ("", ["どの特徴を仕様へ置き、どれを規約へ置くか", '<span class="kindtag out">範囲外</span>', "分け目を裁く基準を定める別の決定"]),
     ("", ["実装の綴りをどこから導くか", '<span class="kindtag out">範囲外</span>', "綴りの導出元を扱う別の決定"]),
     ("", ["knowledge から記入指示への突き合わせ", '<span class="kindtag unv">未確認</span>', "機構を作る別の決定"]),
     ("", ["仕様の執筆に規約が要る場面が今後現れないか", '<span class="kindtag lim">限界</span>',
       "<b>持たない。</b>現れた時点でこの決定を改める"]),
   ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span></div></section>',

 sec("08","関連", "以後の決定は、この関係の上で置き場所を論じる。",
   "", fold("縛る対象と、前後の決定を開く（3件）",
     tbl(["種類", "対象"], [
       ("", ["縛る対象", "仕様・規約・実装の関係"]),
       ("", ["先立つ決定", "理由は論証の連鎖として書く"]),
       ("", ["使う予定", "分け目を裁く基準／仕様は実装の綴りを持たない／knowledge から記入指示への突き合わせ"]),
     ]))),
])

extra = """
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;border-left:3px solid var(--ink);padding-left:.85rem}
.cmp.stack{grid-template-columns:1fr}
.pane .box{display:flex;justify-content:center}
.pane svg{display:block;max-width:100%;height:auto}
.mk{display:inline-flex;align-items:center;gap:.4rem;white-space:nowrap}
.mk .sym{font-size:1.05rem;line-height:1;font-weight:700}
.mk.ok .sym{color:#1B6B4A} .mk.ng .sym{color:#9A3B44}
.keycol{background:#F5EDDF;color:#7A4E12}
.keyrow td{background:#F5EDDF}
.keytag{font-family:var(--mono);font-size:.63rem;color:#7A4E12;background:var(--surface);
        border:1px solid #7A4E12;border-radius:2px;padding:.06em .4em;margin-left:.5rem;white-space:nowrap}
.pickrow td{background:#E9F0F6}
.sub{font-weight:400;font-size:.82rem;color:var(--ink-faint)}
.fold{border:1px solid var(--rule);border-radius:2px;background:var(--surface)}
.fold>summary{cursor:pointer;padding:.7rem .95rem;font-size:.86rem;color:var(--ink-soft);
              list-style:none;display:flex;align-items:center;gap:.5rem}
.fold>summary::before{content:"▸";color:var(--ink-faint);font-size:.8rem}
.fold[open]>summary::before{content:"▾"}
.fold>summary::-webkit-details-marker{display:none}
.fold .scroll{border:none;border-top:1px solid var(--rule);border-radius:0}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --k:1} .mk.ok .sym{color:#79C5A0} .mk.ng .sym{color:#DE9AA1}
  .keycol,.keyrow td{background:#2A2216;color:#D9B674}
  .keytag{color:#D9B674;border-color:#D9B674}
  .pickrow td{background:#172430}}
"""
html = ("<title>規約は層ではなく、実装を導くもう一つの入力とする</title>"
        f"<style>{CSS}\n{TOK}\n{extra}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-convention-is-not-a-layer.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
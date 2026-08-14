import pathlib
S = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
CSS = S.joinpath("newfmt.css").read_text(encoding="utf-8")

def sec(n,t,lead,main,fold=None):
    h=f'<section><h2><span class="num">{n}</span>{t}</h2>'
    if lead: h+=f'<p class="lead">{lead}</p>'
    h+=main
    if fold: h+=fold
    return h+"</section>"
def fold(sm,inner): return f'<details class="fold"><summary>{sm}</summary>{inner}</details>'
def tbl(head,rows):
    hh="".join(f"<th>{c}</th>" for c in head)
    bb="".join(f'<tr class="{r[0]}">'+"".join(f'<td class="cond">{c}</td>' if i==0 else f"<td>{c}</td>"
       for i,c in enumerate(r[1]))+"</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{hh}</tr></thead><tbody>{bb}</tbody></table></div>'
def step(k,l,t): return f'<div class="step {k}"><span class="lbl">{l}</span><span class="txt">{t}</span></div>'
def joint(t): return f'<div class="joint">{t}</div>'
ok='<span class="mk ok"><span class="sym">○</span></span>'
ng='<span class="mk ng"><span class="sym">×</span></span>'

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">同じ特徴なら誰が裁いても同じ答えになる<br><span class="sub">決め手</span></th>
<th>宣言に無い新しい特徴も裁ける</th><th>規則を覚えていられる</th><th>境界の事例を裁ける</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">一文で裁く<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">特徴ごとに一覧を作る</td><td>{ok}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">その都度 advisor に諮る</td><td>{ng}</td><td>{ok}</td><td>{ok}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['同じ特徴なら、誰が裁いても同じ答えになる<span class="keytag">決め手</span>',
      "これが無いと、同じ特徴が判断のたびに違う側へ落ちる。実際そうなっており、この決定はそれを止めるためにある",
      "<b>諮る</b> 相談のたびに答えが変わりうる。今日も同じ問いで違う結論を出した"]),
    ("",["宣言に無い新しい特徴も裁ける",
      "特徴は今後も出てくる。一覧に無いものを裁けないと、結局その場で議論することになる",
      "<b>一覧</b> 列挙していないものは裁けない"]),
    ("",["規則を覚えていられる",
      "書く瞬間に思い出せない規則は、書いたあとの点検でしか効かない。点検は毎回されるとは限らない",
      "<b>一覧</b> 特徴が増えるほど覚えられなくなる"]),
    ("",["境界の事例を裁ける",
      "程度の差しかないもの（速い／遅い、大きい／小さい）は真偽で割れない。割ると閾値を隠すことになる",
      "<b>一文で裁く（採る）</b> 一文は二択なので、程度の差を裁けない"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った","同じ性質の特徴が、判断のたびに違う側へ落ちた。クラス名を仕様に置き（<code>operationName</code>）、実装のまとまりの名前は規約へ落とした（<code>group</code>）。どちらも綴りである"),
  joint("さらに"),
  step("evidence","測った","仕様に、利用者にとって何も変わらない記述が入っている。表部品の <code>bullet</code> と <code>join</code> の優先順位が受け入れ基準にある"),
  joint("だから"),
  step("conclude","言えること","分け目を毎回その場で決めており、規則が無い"),
  joint("ここで置いた前提"),
  step("premise","確かめていない","この一文で、いま迷っている特徴のほとんどを裁ける"),
  joint("合わせると"),
  step("conclude","結論","分け目を一文で固定し、判断のたびに議論しない形にする"),
  joint("ただし"),
  step("counter","反証","「利用者」が誰かは、この製品では一意でない。仕様を読むのも実装を呼ぶのも、人のときと別の仕組みのときがある"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("",["同じ性質の特徴が違う側へ落ちた",'<span class="kindtag unv">実測</span>',
      "<code>operationName</code> と <code>group</code> の扱いを比べた",
      "綴り以外の特徴で、同じ食い違いが起きないと分かったとき"]),
    ("",["仕様に、何も変わらない記述がある",'<span class="kindtag unv">実測</span>',
      "受け入れ基準 <code>bullet-wins-over-join</code>",
      "その記述が利用者にとって何かを変えると分かったとき"]),
    ("",["この一文でほとんどを裁ける",'<span class="kindtag lim">確かめていない</span>',"—",
      "一文で裁けない特徴が続けて出たとき"]),
    ("keyrow",["分け目を一文で固定する",'<span class="kindtag out">Waffle の設計判断</span>',
      "<b>knowledge に該当なし</b>","—"]),
  ])
  + '<p class="foldnote">最後の段に knowledge の裏付けが無い理由 ── '
    'knowledge は「仕様に実装都合の語彙を入れない」とまでは言うが、'
    '<b>何をもって実装都合とするかの判定手順は持たない</b>。'
    'その手順を定めるのは、この製品が仕様と規約という2つの文書を持つことに由来する判断であり、原則からは導かれない。</p>')

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>仕様と規約の分け目を、一文で裁く</h1>'
 '<p class="lede">Waffle では、何ができるかを仕様が、実装がどう在るべきかを規約が宣言する。'
 'この決定は、<b>ある特徴をどちらへ書くかを、どう決めるか</b>を定める。'
 '以前は特徴ごとにその場で議論していた。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">仕様と規約の分け目は、次の一文で裁く。<br>'
  '<b>利用者にとって何が起きるかが変わるなら仕様。コードの並べ方だけが変わるなら規約。</b></p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">規則が無いと、<b>同じ性質の特徴が判断のたびに違う側へ落ちる</b>。'
  '実際、クラス名は仕様に残り、実装のまとまりの名前は規約へ落ちた。どちらも綴りである。</span></div></div>'),

 sec("02","変更前と変更後","特徴ごとの議論が、一文の当てはめに変わる。図は使わない——変わるのは判定の仕方であって、構造ではない。",
  tbl(["特徴","変更前","変更後"],[
    ("",["<code>operationName</code>（クラス名）","使われている箇所が多いので仕様に残す、と判断した",
      "<b>規約。</b>クラス名を変えても、外から見て何も変わらない"]),
    ("",["エラーコード","議論していない",
      "<b>仕様。</b>呼ぶ側がこれで分岐する"]),
    ("",["戻りの形","議論していない",
      "<b>仕様。</b>受け取る側が形に依存している"]),
    ("",["表部品の整形の決まりごと","受け入れ基準に入っている",
      "<b>規約。</b>成果物の見た目の決まりで、何ができるかは変わらない"]),
  ])),

 sec("03","理由",None,reason,reason_fold),

 sec("04","判断を分けた軸",
  "採る案は3つの条件を満たし、境界の事例を裁けないことだけを落とす。",
  axis, axis_fold),

 sec("05","付随して決めたこと","一文を当てるときの測り方と、裁けなかったときの行き先を同時に決める。",
  tbl(["論点","決定"],[
    ("",["書きすぎを止める測り方",
      "ある記述を消して、利用者にできることが1つも減らないなら、それは仕様ではない"]),
    ("",["「利用者」とは誰か",
      "その操作を呼ぶ側。人のときも、別の仕組みのときもある"]),
    ("",["一文で裁けない特徴が出たとき",
      "その場で決めない。knowledge へ問い、無ければ Waffle の設計判断として別に決める"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("",["書きすぎを止める測り方",
        "一文は下限（潰しすぎ）を止めるが、上限（書きすぎ）は止めない。消して減らないものを残すと、仕様が実装の転記へ寄っていく"]),
      ("",["「利用者」とは誰か",
        "この製品では、仕様を読むのも実装を呼ぶのも、人と別の仕組みの両方がありうる。誰かを固定すると裁けない特徴が増える"]),
      ("",["裁けない特徴が出たとき",
        "この決定は裁く道具であって、裁けないものを裁く権限を与えるものではない。その場で決めると、規則を作った意味が消える"]),
    ]))),

 sec("06","答えないこと","個別の移動と、程度の差しかない特徴は、この決定では扱わない。",
  tbl(["項目","種別","行き先"],[
    ("",["いま仕様に入っている記述のうち、どれを規約へ移すか",'<span class="kindtag out">範囲外</span>',
      "この決定は裁き方だけを定める。移動は洗い出しの作業として別に行う"]),
    ("",["綴りの導出元をどこが宣言するか",'<span class="kindtag out">範囲外</span>',
      "この一文を当てると規約側になる。どう宣言するかは別の決定で定める"]),
    ("",["程度の差しかない特徴（速い／遅い等）",'<span class="kindtag lim">限界</span>',
      "<b>行き先を持たない。</b>閾値を条件として書けるなら仕様、書けないなら裁かない。実例が出た時点でこの決定を見直す"]),
    ("",["何件が規約側へ動くか",'<span class="kindtag unv">未確認</span>',
      "洗い出しの作業で数える"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span></div></section>',

 sec("08","関連","この一文は、仕様と規約が同じ格であるという関係の上に立つ。","",
  fold("縛る対象と、前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("",["縛る対象","仕様と規約に何を書くか。以後、特徴の置き場所はこの一文で決まる"]),
      ("",["先立つ決定","規約は層ではなく、実装を導くもう一つの入力とする（承認済み）"]),
      ("",["この決定を使う予定","仕様は実装の綴りを持たない"]),
      ("",["この決定が正した私の誤り",
        "<code>operationName</code> の扱いを「使われている箇所が多いから」という数え上げで決めようとした"]),
    ]))),
])

extra = """
.lead{font-family:var(--serif);font-size:1.02rem;font-weight:600;line-height:1.65;border-left:3px solid var(--ink);padding-left:.85rem}
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
.foldnote{font-size:.84rem;line-height:1.75;color:var(--ink-soft);padding:.8rem .95rem;border-top:1px solid var(--rule-soft)}
.foldnote b{color:var(--ink)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  .mk.ok .sym{color:#79C5A0} .mk.ng .sym{color:#DE9AA1}
  .keycol,.keyrow td{background:#2A2216;color:#D9B674}
  .keytag{color:#D9B674;border-color:#D9B674} .pickrow td{background:#172430}}}
"""
html = ("<title>仕様と規約の分け目を、一文で裁く</title>"
        f"<style>{CSS}\n{extra}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-split-rule.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
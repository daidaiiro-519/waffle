import json, pathlib
S = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
CSS = S.joinpath("newfmt.css").read_text(encoding="utf-8")
TOK = S.joinpath("fig_tokens.txt").read_text(encoding="utf-8")
FIG = json.loads(S.joinpath("fig_schema.json").read_text(encoding="utf-8"))

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
<thead><tr><th>案</th><th>主張が揃った語彙で残る</th><th>描き方を変えても宣言が動かない</th>
<th>囲みや入れ子を主張を問わず組み合わせられる</th><th>いまの79件をそのまま使える</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">主張を軸にする<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">描き方の指定のまま</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("",["主張が、揃った語彙で残る",
      "同じ主張が別の言い回しで書かれると、図どうしを揃えられない。実測では「〜を示す」「〜を決める」「〜が行き来する」が混在していた",
      "<b>描き方の指定のまま</b> 意図が自由記述なので、語彙が揃わない"]),
    ("",["描き方を変えても宣言が動かない",
      "描き方は見せ方の都合で変わる。宣言が一緒に動くと、同じ内容の図が書き手ごとに違う宣言になる",
      "<b>描き方の指定のまま</b> 向きや囲みの置き場所が宣言に書かれているので、描き方を変えると宣言が動く"]),
    ("",["囲みや入れ子を、主張を問わず組み合わせられる",
      "組み合わせられないと、主張ごとに特別な書き方を覚えることになる",
      "<b>描き方の指定のまま</b> 囲みがひとつの主張の専用になっており、他の主張で使うと規則が拒否する"]),
    ("",["いまの79件をそのまま使える",
      "既にある宣言を書き換えずに済むなら、移行の手間も写し間違いも起きない",
      "<b>主張を軸にする（採る）</b> 79件を1件ずつ人が判断して写す必要がある"]),
  ])
  + '<p class="foldnote">この記録を書き直したとき、<b>どの条件が決め手だったかは特定できなかった</b>。'
    '当時は決め手を書く欄が無く、後から選ぶと再構成になる。'
    '分かっているのは、<b>採る案が満たさない条件が1つある</b>ことと、それを承知で採ったこと。</p>')

reason = '<div class="chain">' + "".join([
  step("evidence","測った","宣言79件すべてが、その図の意図を自由記述で持っていた。ただし描画はそれを一切読まず、別の場所に置かれた描き方の名前だけで描いていた"),
  joint("だから"),
  step("conclude","言えること","主張と描き方は別々に宣言され、互いを縛っていない"),
  joint("一方で"),
  step("evidence","測った","描き方の指定が、宣言と Schema の両方に散っている。同じ「向き」が両側にあり、Schema 側にはさらに20あまりの指定が並ぶ"),
  joint("さらに"),
  step("evidence","測った","囲みが、ひとつの主張の専用になっていた。他の主張で囲もうとすると規則が拒否する"),
  joint("合わせると"),
  step("conclude","結論","宣言の軸を主張へ移し、描き方の指定は宣言から出して、主張から従属して決まるようにする"),
  joint("ただし"),
  step("counter","反証","いまの79件はそのまま使えなくなる。1件ずつ人が判断して写すことになる"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("",["79件すべてが意図を自由記述で持つ",'<span class="kindtag unv">実測</span>',"宣言79件の走査","描画が意図を読むようになったとき"]),
    ("",["描き方の指定が両側に散っている",'<span class="kindtag unv">実測</span>',"宣言と Schema の両方の指定を数えた","指定が片側へ寄せられたとき"]),
    ("",["囲みが主張の専用になっている",'<span class="kindtag unv">実測</span>',"他の主張で囲みを使い、規則が拒否することを確かめた","囲みがどの主張でも使えるようになったとき"]),
    ("keyrow",["軸を主張へ移す",'<span class="kindtag out">Waffle の設計判断</span>',"<b>knowledge に該当なし</b>","—"]),
  ])
  + '<p class="foldnote">最後の段に knowledge の裏付けが無い理由 ── '
    '図の宣言をどう組むかは、この製品が図を持つと決めたことに由来する判断であり、'
    '確立された原則から導かれるものではない。</p>')

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>図の宣言を、主張を軸にした形へ置き換える</h1>'
 '<p class="lede">Waffle の図は、document.json に書かれた宣言から描かれる。'
 'この決定は、<b>その宣言が何を軸に組まれるか</b>を定める。'
 '以前は描き方の名前（流れ図・順序図など）が軸だった。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">図の宣言の軸を、描き方の指定から主張へ移す。'
  '描き方の指定は宣言から出し、主張から従属して決まるようにする。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">主張と描き方が<b>別々に宣言され、互いを縛っていない</b>。'
  '79件すべてが意図を自由記述で持つのに、描画はそれを読んでいない。</span></div></div>'),

 sec("02","変更前と変更後","宣言から描き方の指定が消え、主張がひとつ立つ。読み方と注釈はそのまま残る。",
  fold("変更点を表で見る（4件）",
    tbl(["何が","変更前","変更後"],[
      ("",["主張の持ち方","自由記述の意図","語彙から1つ選ぶ"]),
      ("",["描き方の指定","宣言と Schema の両方に散在","宣言から消える。主張から決まる"]),
      ("",["囲み","ひとつの主張の専用","どの主張でも同じ形で書ける"]),
      ("",["読み方と注釈","持つ","そのまま持つ"]),
    ]))
  + '<p class="fignote">この2枚は、前の決定で定めた記法で描いている。</p>'
  + '<div class="cmp stack">'
  + f'<div class="pane"><span class="pane-label b">変更前</span><div class="box">{FIG["before"]}</div></div>'
  + f'<div class="pane"><span class="pane-label a">変更後</span><div class="box">{FIG["after"]}</div></div>'
  + '</div>'),

 sec("03","理由",None,reason,reason_fold),

 sec("04","判断を分けた軸",
  "採る案は3つの条件を満たし、1つを落とす。落とすのは、いまの79件をそのまま使えることだけ。",
  axis, axis_fold),

 sec("05","付随して決めたこと","主文だけでは読み方が定まらない3点を、同時に確定させた。",
  tbl(["論点","決定"],[
    ("",["主張の持ち方","語彙から1つ選ぶ。自由記述の意図は置き換わる"]),
    ("",["描き方の指定","宣言から出す。向きも囲みの置き場所も、主張から決まる"]),
    ("",["読み方と注釈","残す。人が図を読むために要る"]),
  ]),
  fold("定めないとどうなるかを開く（3件）",
    tbl(["論点","定めないと"],[
      ("",["主張の持ち方","同じ主張が別の言い回しで書かれ、揃えられない"]),
      ("",["描き方の指定","軸を変えても、描き方の指定が別の鍵として残る"]),
      ("",["読み方と注釈","図の読み方を運ぶ場所が消える。要素を名指しした注釈は、図に載せきれないことを結ぶ唯一の場所"]),
    ]))),

 sec("06","答えないこと","語彙の中身は仕様で決める。79件の写しは着手の段で決める。",
  tbl(["項目","種別","行き先"],[
    ("",["語彙の名前・欄の名前・条件の書き方",'<span class="kindtag out">範囲外</span>',
      "仕様で決める。ここで決めるのは軸だけ"]),
    ("",["79件をいつ誰が写すか",'<span class="kindtag unv">未確認</span>',
      "実装に着手する段で決める。写し方（1件ずつ人が判断する）は決まっている"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span>'
 '<span class="m">新しい形へ書き換えたので、改めて承認を受ける。決定の内容は変えていない。</span>'
 '</div></section>',

 sec("08","関連","前の決定が定めた語彙の上に立ち、次は実装の順を決める。","",
  fold("縛る対象と、前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("",["縛る対象","図の宣言の形。以後の図はこの軸で書かれる"]),
      ("",["先行する決定","図の語彙を、描き方から主張へ移す（承認済み）"]),
      ("",["後続の決定","描画をどう作り直すか。実装の綴りの扱いが決まってから起こす"]),
      ("",["この決定が正した私の誤り","既存の宣言を見ずに「主張が記録されない」と書いた／組み合わせが一般に効くと思っていた"]),
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
  .keyrow td{background:#2A2216} .pickrow td{background:#172430}}}
"""
html = ("<title>図の宣言を、主張を軸にした形へ置き換える</title>"
        f"<style>{CSS}\n{TOK}\n{extra}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-schema.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
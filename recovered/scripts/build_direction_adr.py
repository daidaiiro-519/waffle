import sys, pathlib
sys.path.insert(0,"/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

D = "<code>architecture-dependency-direction</code>"

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">同じ対応が1か所にしかない<br><span class="sub">決め手</span></th>
<th>knowledge を消費者ごと持ち出さずに済む</th><th>読む側を増やすとき knowledge を触らない</th>
<th>配置先を1件引くだけで決められる</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">読む側だけが宣言する<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">knowledge 側だけが宣言する</td><td>{ok}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">両方が宣言する<br><span class="sub">いまのまま</span></td>
<td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['同じ対応が1か所にしかない<span class="keytag">決め手</span>',
      "対応が2か所にあると食い違う。実際に3つの advisor で食い違っており、"
      "どちらが正かをいま決められない",
      "<b>両方が宣言する</b> 2か所にある"]),
    ("",["knowledge を消費者ごと持ち出さずに済む",
      "knowledge は確立された概念を持つ。別のプロジェクトへ持ち出すとき、"
      "このプロジェクトの advisor の名前が付いたまま出ていく",
      "<b>knowledge 側だけ</b>／<b>両方</b> どちらも knowledge が消費者の名前を持つ"]),
    ("",["読む側を増やすとき knowledge を触らない",
      "advisor を1つ増やすたびに knowledge を1件ずつ書き換えるなら、"
      "増やす手間が knowledge の件数に比例する",
      "<b>knowledge 側だけ</b>／<b>両方</b> どちらも knowledge を書き換えることになる"]),
    ("",["配置先を1件引くだけで決められる",
      "描画のとき、その knowledge をどこへ置くかを決める必要がある",
      "<b>読む側だけが宣言する（採る）</b> 読む側を全部走査して、"
      "誰が参照しているかを集めることになる"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "宣言が<b>両方向にある</b>。knowledge の側が「私は誰に読まれるか」を持ち、"
    "読む側も「私は何を読むか」を持っている"),
  joint("その2つを突き合わせた"),
  step("evidence","測った",
    "5つの advisor のうち<b>3つで食い違っていた</b>（10対9・7対5・8対7）。"
    "しかも実際に配られている実体は、knowledge 側の宣言に従っている"),
  joint("だから"),
  step("conclude","言えること",
    "読む側の宣言は<b>表示だけで、実効を持っていない</b>。"
    "同じ対応が2か所にあり、どちらが正かを決める根拠がない"),
  joint("ここで置いた前提"),
  step("premise","確かめていない",
    "knowledge は、それを読む advisor の構成より変わりにくい"),
  joint("拠り所に当てると"),
  step("conclude","言えること",
    "依存は変わりにくい側へ向ける。<b>knowledge が読む側の名前を持つのは、逆向きである</b>"),
  joint("合わせると"),
  step("conclude","結論",
    "読む側だけが宣言し、knowledge は自分を読む相手を知らない形にする"),
  joint("ただし"),
  step("counter","反証",
    "配置先を決めるとき、読む側を<b>全部走査する</b>ことになる。"
    "1件引くより遅く、走査の範囲を取り違えると配り漏れる。"
    "いまは1件引けば済んでいる"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("",["宣言が両方向にある",'<span class="kindtag unv">実測</span>',
      "knowledge 側の欄と、読む側の欄をそれぞれ数えた","—"]),
    ("keyrow",["3つで食い違う",'<span class="kindtag unv">実測</span>',
      "5つの advisor について、両側の件数と配置された実体を突き合わせた",
      "数え方を変えると一致するとき。件数で比べており、中身までは照合していない"]),
    ("",["knowledge のほうが変わりにくい",'<span class="kindtag lim">確かめていない</span>',"—",
      "advisor の構成より先に knowledge が入れ替わったとき"]),
    ("",["依存は変わりにくい側へ向ける",'<span class="kindtag unv">knowledge</span>',
      f"{D} ── 「依存とは A が B を知っているという関係」「安定性は、"
      "頻繁に変わるものとめったに変わらないものを分離することで保たれる」",
      "この knowledge が扱うのはコードの層であり、文書どうしの参照を"
      "同じ依存とみなす段は Waffle の判断である"]),
  ])
  + '<p class="foldnote">拠り所の使い方 ── '
    f'{D} から引いたのは<b>判断の形</b>（依存は変わりにくい側へ向ける）だけである。'
    'この knowledge が挙げる例と分類はすべてコードの層で、'
    '<b>文書どうしの参照を同じ依存として扱ってよいかまでは定めていない</b>。'
    'その一段は Waffle の判断として置いている。</p>')

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>knowledge は、自分を読む相手を知らない</h1>'
 '<p class="lede">いま knowledge は「私は誰に読まれるか」を持ち、読む側も「私は何を読むか」を持っている。'
 '同じ対応が2か所にあり、<b>実際に3つの advisor で食い違っている</b>。'
 'この記録は、宣言を読む側の一方向へ寄せる。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、knowledge に読む相手を持たせない。'
  '<b>読む側（advisor と Orchestrator）だけが、自分が読む knowledge を宣言する。</b>'
  '配置先は、その宣言から導く。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">同じ対応が2か所にあり、<b>5つの advisor のうち3つで食い違っていた</b>。'
  'しかも実際に配られている実体は knowledge 側の宣言に従っており、'
  '読む側の宣言は実効を持っていない。</span></div></div>'),

 sec("02","変更前と変更後",
  "この決定が変えるのは、<b>誰が対応を宣言するか</b>である。knowledge の中身は変えない。",
  tbl(["","変更前 ── 両方向に宣言がある","変更後 ── 読む側だけが宣言する"],[
    ("keyrow",["対応を宣言する場所","knowledge 側と読む側の<b>2か所</b>",
      "<b>読む側の1か所</b>"]),
    ("",["実際に配る根拠","knowledge 側の宣言","<b>読む側の宣言</b>"]),
    ("",["2つの宣言の食い違い","5つの advisor のうち3つでずれている",
      "<b>宣言が1つなので、ずれる先が無い</b>"]),
    ("",["読む側を1つ増やすとき","knowledge を1件ずつ書き換える",
      "<b>増やした側が宣言する。</b>knowledge は動かない"]),
    ("",["別のプロジェクトへ持ち出すとき","このプロジェクトの advisor 名が付いたまま出る",
      "<b>knowledge は消費者を知らないので、そのまま出せる</b>"]),
  ])),

 sec("03","理由",
  "同じ対応が2か所にあり、3つの advisor で食い違っていた。"
  "<b>読む側の宣言は表示だけで、実効を持っていない。</b>",
  reason, reason_fold),

 sec("04","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、"
  "<b>配置先を決めるのに読む側を全部走査することになる</b>。",
  axis, axis_fold),

 sec("05","付随して決めたこと",
  "宣言を一方向にすると、いま宣言から引いていた3つの経路を引き直す必要が出る。",
  tbl(["論点","決定"],[
    ("keyrow",["配置先をどう決めるか",
      "読む側の宣言を走査して集める。<b>走査の範囲を明示する</b>"]),
    ("",["セッション開始時の注入元",
      "Orchestrator が宣言したものから引く。knowledge の側からは引かない"]),
    ("",["残っている単数形の欄",
      "1件だけ古い単数形が残っている。この移行で落とす"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("keyrow",["配置先をどう決めるか",
        "走査で集める形にすると、<b>どこを走査するかを書かない限り、"
        "その規則は実行時に参照先を持たない</b>。"
        "取得経路を明示しない比較の規則は、言明として存在するだけになる"]),
      ("",["セッション開始時の注入元",
        "いまの注入は knowledge 側の宣言を filter している。"
        "向きを変えるなら、この経路も同時に変えないと、"
        "廃止したはずの宣言が実効を持ち続ける"]),
      ("",["残っている単数形の欄",
        "複数形へ移行した際の取り残し。廃止する欄なので、"
        "移行のついでに落とす。残すと、どちらの欄を読むかが分かれる"]),
    ]))),

 sec("06","答えないこと",
  "宣言の書き方と、既存の書き換えは、この決定では扱わない。",
  tbl(["項目","種別","行き先"],[
    ("",["Orchestrator が宣言する欄の形",'<span class="kindtag out">範囲外</span>',
      "実装に着手する段で決める"]),
    ("",["既存の knowledge をいつ書き換えるか",'<span class="kindtag out">範囲外</span>',
      "移行の段取りは別に決める"]),
    ("keyrow",["食い違っている3件は、どちらが正か",'<span class="kindtag unv">未確認</span>',
      "<b>件数で比べており、中身までは照合していない。</b>"
      "宣言を一方向へ寄せるとき、1件ずつ確かめることになる"]),
    ("",["走査の速さが実用に足りるか",'<span class="kindtag unv">未確認</span>',
      "測っていない。反証に挙げた通り、1件引くより遅い"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">未承認</span></div></section>',

 sec("08","関連","この決定は、knowledge を書き直す前に要る。","",
  fold("縛る対象と、前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象",
        "knowledge が持てる欄と、配置・注入の経路"]),
      ("",["引く knowledge",
        f"{D} ── 判断の形だけを引く。文書どうしの参照へ当てる段は Waffle の判断"]),
      ("",["この決定を使う予定",
        "仕様と実装の抽象境界の knowledge を、新しい語彙で起こし直す。"
        "先に向きを決めないと、廃止する形で新規を書くことになる"]),
      ("",["先立つ決定",
        "規約は層ではなく、実装を導くもう一つの入力とする（承認済み）"]),
    ]))),
])

html = ("<title>knowledge は、自分を読む相手を知らない</title>"
        f"<style>{CSS}\n{extra}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-knowledge-reference-direction.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
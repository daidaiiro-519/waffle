import sys, pathlib, json
sys.path.insert(0,"/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
S = pathlib.Path("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad")
FIGS = json.loads((S/"vocab_figs.json").read_text(encoding="utf-8"))["svgs"]
FIGCSS = (S/"vocab_figcss.txt").read_text(encoding="utf-8")

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">その図が何を主張しているかが document に残る<br><span class="sub">決め手</span></th>
<th>上流の構文が変わっても影響しない</th><th>書き手が描き方を選ばずに済む</th><th>移す手間がかからない</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">主張の名前へ移す<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">描き方の名前のまま</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['その図が何を主張しているかが document に残る<span class="keytag">決め手</span>',
      "残らないと、読み手は図を見て主張を推測することになる。推測は外れる（実測で12枚中3枚）",
      "<b>描き方のまま</b> 残るのは描き方だけ"]),
    ("",["上流の構文が変わっても影響しない",
      "上流の都合で名前が変わると、こちらの語彙が上流の版に縛られる",
      "<b>描き方のまま</b> 実際に影響した。使用0枚の名前が、上流で旧構文になったまま残っている"]),
    ("",["書き手が描き方を選ばずに済む",
      "描き方を選ばせると、同じ主張が書き手ごとに違う名前で残る",
      "<b>描き方のまま</b> 書き手が選ぶ"]),
    ("",["移す手間がかからない",
      "既にあるものを全部書き換える変更は、途中で止まると新旧が混ざる",
      "<b>主張の名前へ移す（採る）</b> 部品18のうち5・図180枚・受け入れ基準が対象になる"]),
  ])
  + '<p class="foldnote">両案が満たすので落とした条件 ── '
    '<b>名前の粒度は上げられる</b>。どちらの案でも名前は増やせるので、判断が分かれない。</p>')

ba = f'''<div class="cmp">
<div class="pane"><span class="pane-label b">変更前 ── 1つの名前が6種類の主張を担う</span>
<div class="box">{FIGS[0]}</div></div>
<div class="pane"><span class="pane-label a">変更後 ── 主張が名前になる</span>
<div class="box">{FIGS[1]}</div></div></div>
<p class="fignote">この2枚は、<b>決めようとしている記法そのもの</b>で描いている。
外側の主張は「対応」、左の面は「階層」、右の面は「つながり」の宣言。面ごとに違う主張を入れられる。</p>'''

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "1つの名前が6種類の主張を担っている。描かれた図180枚のうち125枚が同じ名前で、"
    "内訳は条件による選択62・向きのある関係30・区画への所属21・順序7・分類6"),
  joint("だから"),
  step("conclude","言えること",
    "document に残るのは描き方だけで、<b>主張は残らない</b>。読み手は図を見て推測するしかない"),
  joint("その推測を確かめた"),
  step("evidence","測った",
    "125枚を機械で主張ごとに分け、無作為12枚を手で確かめたところ<b>3枚が誤り</b>だった"),
  joint("一方で"),
  step("evidence","測った",
    "名前が上流の構文名のまま置かれている。使用0枚の名前が部品名に残り、"
    "同梱の指針自身が「その構文は使用しない」と定めている"),
  joint("だから"),
  step("conclude","言えること",
    "中核の領域が、上流のモデルに従属している。処方はモデル変換装置を置くこと"),
  joint("合わせると"),
  step("conclude","結論",
    "図の部品名の軸を、描き方から<b>何を主張するか</b>へ移す"),
  joint("ただし"),
  step("counter","反証",
    "名前を変えるだけでは依存は消えない。描画の実装が業務の層に置かれ、そこで上流の構文を組み立てている。"
    "改名すると、依存が名前から見えなくなるだけになる"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（5件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["1つの名前が6種類を担う",'<span class="kindtag unv">実測</span>',
      "図180枚の全数分類（Orchestrator）","分類の付け方を変えると6種類に割れなくなったとき"]),
    ("",["推測は外れる",'<span class="kindtag unv">実測</span>',
      "125枚から無作為12枚を抽出し手で照合","抽出をやり直して誤りが出なかったとき。確かめたのは12枚のみ"]),
    ("",["名前が上流の構文名のまま",'<span class="kindtag unv">実測</span>',
      "部品名の一覧と、同梱の指針の記述","上流がその構文を再び使い始めたとき"]),
    ("",["中核が上流のモデルに従属している",'<span class="kindtag unv">knowledge</span>',
      "<code>context-integration</code> のアンチパターン／<code>ubiquitous-language</code>（ddd-advisor 経由）",
      "この領域が中核でないと判定されたとき"]),
    ("",["依存は名前から見えなくなるだけ",'<span class="kindtag unv">実測</span>',
      "描画の実装の置き場所（tech-lead-advisor 経由）","置き場所が先に直されたとき"]),
  ]))

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>図の語彙を、描き方の名前から主張の名前へ移す</h1>'
 '<p class="lede">図の部品は、どう描くかで名付けられていた。'
 'その結果、<b>図が何を主張しているかは document のどこにも残らない</b>。'
 'この記録は、名前の軸を主張へ移す。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">図の部品名を、描き方の名前から'
  '<b>何を主張するか</b>へ置き換える。書ける形は固定し、どの欄を書けるかは主張が決める。'
  '描き方は主張から従属して決まる。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">いまの名前では<b>主張が document に残らない</b>。'
  '残らないものは、読み手が推測するしかない。実測では12枚中3枚で推測が外れた。</span></div></div>'),

 sec("02","変更前と変更後",
  "document に残るものが変わる。<b>描き方だけが残る状態から、主張が残る状態へ。</b>",
  ba),

 sec("03","理由",
  "1つの名前が6種類の主張を担っており、主張そのものはどこにも残っていない。"
  "名前を上流の構文から借りていることが原因で、<b>改名だけでは依存は消えない</b>。",
  reason, reason_fold),

 sec("04","判断を分けた軸",
  "採る案は3つの条件を満たし、移す手間を落とす。既にある180枚が対象になる。",
  axis, axis_fold),

 sec("05","付随して決めたこと",
  "主文だけでは読み方が定まらない4点。<b>定めないと何が起きるか</b>を並べて決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["主張の一覧","関係7・量9の16。既に確立した枠組みから採る"]),
    ("",["書ける形","欄は3つ、書ける名前は18。主張ごとに形を変えない"]),
    ("",["入れ子","置くものは、宣言そのものを中に持てる"]),
    ("",["Markdown","従来どおり Mermaid へ変換して出す"]),
  ]),
  fold("定めないと何が起きるかを開く（4件）",
    tbl(["論点","定めないと"],[
      ("keyrow",["主張の一覧",
        "自分で分類を作ると、置き換えたい語彙の痕跡から語彙を再生産する"]),
      ("",["書ける形","主張の数だけ形が増え、記法ではなく品揃えになる"]),
      ("",["入れ子","面の中身が名前の文字列で止まり、変更前と変更後が書けない"]),
      ("",["Markdown","Mermaid をやめる決定と読まれる"]),
    ]))),

 sec("06","答えないこと",
  "表記・移行・範囲の広げ方は、この決定では扱わない。",
  tbl(["項目","種別","行き先"],[
    ("",["16の主張それぞれの日本語表記",'<span class="kindtag out">範囲外</span>',
      "語そのものは仕様の段で確定する"]),
    ("",["既存180枚をいつ移すか",'<span class="kindtag out">範囲外</span>',
      "移行の段取りは、実装に着手する段で決める"]),
    ("",["文章の部品を同じ枠で扱うか",'<span class="kindtag out">範囲外</span>',
      "変更の理由が違う。別の論点として起こす"]),
    ("",["描画の実装の置き場所",'<span class="kindtag lim">限界</span>',
      "<b>この決定では直らない。</b>反証に挙げたとおり、改名は依存を消さない。別の決定を要する"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span>'
 '<span class="k">誰が</span><span class="m">daidaiiro</span>'
 '<span class="k">いつ</span><span class="m">2026-08-13</span>'
 '<span class="m">記法と16の主張を実物で確かめたうえで承認。'
 'その後、決めた記録の形へ書き直したうえで置いている。</span></div></section>',

 sec("08","関連","この決定は、図を持つ document と描画の実装の全体に及ぶ。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象",
        "schema の描画の宣言／描画のユースケースの受け入れ基準／図を持つ document 180枚"]),
      ("",["先立つ決定","関係は記号ではなく言葉で表す／Mermaid は下限であって上限ではない"]),
      ("",["後続の決定","図の宣言を、主張を軸にした形へ置き換える（承認済み）"]),
      ("",["残る依存","描画の実装が業務の層に置かれている。この決定では直らない"]),
      ("",["この決定を使う予定","決定記録が持つ図は、この語彙で描く"]),
    ]))),
])

html = ("<title>図の語彙を、描き方の名前から主張の名前へ移す</title>"
        f"<style>{CSS}\n{extra}\n{FIGCSS}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-figure-vocabulary.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")
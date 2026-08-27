import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

K = "<code>operation-contract-closes-invariants</code>"

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">判断が、それに要るデータのある場所にある<br><span class="sub">決め手</span></th>
<th>宣言されていない操作に依存しない</th><th>ユースケースが調整だけを担う</th>
<th>いまの実装を動かさずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">コマンドを、データのある場所へ戻す<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">いまのまま置く</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">Document に全部持たせる</td><td>{ng}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['判断が、それに要るデータのある場所にある<span class="keytag">決め手</span>',
      "骨格の形を知っているのは Schema だけである。"
      "他所に置くと、Schema を読みに行く処理を書くことになり、"
      "Schema が変わったときに直す場所が2つになる",
      "<b>いまのまま</b> 判断がユースケースにある<br>"
      "<b>Document に全部</b> 作られる側が、自分の骨格の形を知ることになる"]),
    ("",["宣言されていない操作に依存しない",
      "宣言に無い操作へ依存すると、その操作が変わっても誰も気づけない",
      "<b>いまのまま</b> 値を埋めるコマンドが宣言に無いのに、"
      "適合の判定がその結果の永続化を前提にしている"]),
    ("",["ユースケースが調整だけを担う",
      "調整と判断が同じ場所にあると、判断を再利用するときにユースケースごと呼ぶことになる",
      "<b>いまのまま</b> 骨格の組み立てがユースケースの中にある"]),
    ("",["いまの実装を動かさずに済む",
      "動かす範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>データのある場所へ戻す（採る）</b>／<b>Document に全部</b> どちらも実装を動かす"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "Schema の実装は<b>27行でクラス宣言だけ</b>、宣言されたコマンドは<b>0件</b>。"
    "一方、骨格を作るユースケースの実装は<b>412行</b>ある"),
  joint("だから"),
  step("conclude","言えること",
    "骨格の形を知っている唯一の相手が空で、<b>判断が外へ出ている</b>"),
  joint("Document の側も見た"),
  step("evidence","測った",
    "Document のコマンド4件は、名前がユースケースと同じである。"
    "しかも <code>create</code> の説明が「schemaRef と documentId から骨格を生成する」で、"
    "<b>作られる側が自分を作ることになっている</b>"),
  joint("さらに"),
  step("evidence","測った",
    "<b>値を埋めるコマンドが宣言に無い</b>。"
    "それでいて適合を判定するコマンドの説明が「判定結果の永続化は別途行う」と、"
    "宣言されていない操作を前提にしている"),
  joint("拠り所に当てると"),
  step("conclude","言えること",
    "呼び出せる操作を持つのは業務ユースケース・業務サービス・集約のコマンドの3つである。"
    "<b>集約が持つべき操作が、ユースケースの側にある</b>"),
  joint("合わせると"),
  step("conclude","結論",
    "コマンドを、判断に要るデータのある場所へ戻す。ユースケースは調整だけを担う"),
  joint("ただし"),
  step("counter","反証",
    "単体の取得は、Document の値と Schema の読み方の指針を<b>組み合わせて</b>返している。"
    "Document のコマンドだけでは完結せず、ユースケースに残る仕事がある。"
    "「単体の操作はすべて集約のコマンド」とは言い切れない"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（5件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["Schema が27行・コマンド0件、ユースケースが412行",
      '<span class="kindtag unv">実測</span>',
      "実装の行数と、集約が宣言するコマンドの数を数えた","—"]),
    ("",["Document のコマンドがユースケースの写し",'<span class="kindtag unv">実測</span>',
      "4件の名前と説明を読んだ","名前が同じでも中身が違うと分かったとき"]),
    ("",["値を埋めるコマンドが宣言に無い",'<span class="kindtag unv">実測</span>',
      "コマンドの一覧と、適合を判定するコマンドの説明","—"]),
    ("",["呼び出せる操作を持つのは3つ",'<span class="kindtag unv">knowledge</span>',
      f"{K}","—"]),
    ("",["判断はデータのある場所へ置く",'<span class="kindtag out">Waffle の設計判断</span>',
      "<b>knowledge に該当なし</b>","—"]),
  ])
  + '<p class="foldnote">最後の段に knowledge の裏付けが無い理由 ── '
    f'{K} は<b>どこに操作が付くか</b>までは述べるが、'
    '同じ集約の中で<b>どの判断をコマンドに持たせるか</b>は持たない。'
    'データのある場所へ置くという指針は、この製品の側で置いている。</p>')

item_tbl = tbl(["","変更前","変更後"],[
 ("keyrow",["Schema の実装","<b>27行。</b>クラス宣言だけ","判断を持つ"]),
 ("",["Schema が宣言するコマンド","<b>0件</b>","<b>3件</b>"]),
 ("",["Document が宣言するコマンド","4件。うち2件は Schema の仕事",
   "<b>4件。</b>値を埋める・値を取り出すを含む"]),
 ("",["骨格を作るユースケースの実装","<b>412行。</b>組み立てをここでやる","調整だけ"]),
 ("",["ユースケースの数","30件","<b>変えない。</b>無くすのではなく中身を移す"]),
 ("",["実装の domain/services","<b>24件</b>（仕様に書かれた業務サービスは5件）","移し先を1件ずつ判定する"]),
])

cmd_tbl = tbl(["コマンド","変更前","変更後","理由"],[
 ("keyrow",["骨格を作る","Document の <code>create</code>","<b>Schema</b>",
   "骨格の形を知っているのは Schema だけ"]),
 ("keyrow",["適合を判定する","Document の <code>validate</code>","<b>Schema</b>",
   "判定の基準を持つのは Schema"]),
 ("",["新しい版を切る","（宣言に無い）","<b>Schema</b>",
   "版の集合を守るのは Schema"]),
 ("",["値を埋める","<b>（宣言に無い）</b>","<b>Document</b>",
   "自分の中身を書き換える。入力の値を受け取るだけ"]),
 ("",["値を取り出す","（宣言に無い）","<b>Document</b>",
   "自分の値を返すだけ"]),
 ("",["描く","Document の <code>render</code>","<b>Document</b>","変えない"]),
 ("",["終端化する","Document の <code>supersede</code>","<b>Document</b>","変えない"]),
])

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>コマンドを、判断に要るデータのある場所へ戻す</h1>'
 '<p class="lede">Schema の実装は27行でクラス宣言だけ、コマンドは0件。'
 '一方で骨格を作るユースケースは412行ある。'
 '<b>骨格の形を知っている唯一の相手が空で、判断が外へ出ている。</b></p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>集約のコマンドを、その判断に要るデータのある場所へ置く</b>。'
  'Schema は「骨格を作る・新しい版を切る・適合を判定する」を持ち、'
  'Document は「値を埋める・値を取り出す・描く・終端化する」を持つ。'
  'ユースケースは調整だけを担う。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt">骨格の形を知っているのは Schema だけである。'
  'いまは Document の <code>create</code> が「schemaRef と documentId から骨格を生成する」と述べており、'
  '<b>作られる側が自分を作ることになっている</b>。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>コマンドの持ち主</b>である。ユースケースの数は変えない。",
  '<h3 class="sub-h">項目で見る</h3>' + item_tbl +
  '<h3 class="sub-h">コマンドで見る</h3>' + cmd_tbl),

 sec("03","理由",
  "骨格の形を知っている唯一の相手が空で、判断が外へ出ている。"
  "<b>値を埋めるコマンドは宣言にすら無い。</b>",
  reason, reason_fold),

 sec("04","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>実装を動かすことになる</b>。",
  axis, axis_fold),

 sec("05","付随して決めたこと",
  "コマンドを移すと、ユースケースに何が残るかが決まる。3点を同時に決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["ユースケースをどうするか",
      "<b>無くさない。</b>中身を移し、調整だけを残す"]),
    ("",["単体の取得はどちらか",
      "<b>両方。</b>値は Document、読み方の指針は Schema。束ねるのはユースケース"]),
    ("",["実装の domain/services 24件",
      "移し先を1件ずつ判定する。この決定では判定しない"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("keyrow",["ユースケースをどうするか",
        "ユースケースが在ること自体は誤りではない。誤りは、判断がその中にあることである。"
        "調整と判断を分ければ、判断は他からも呼べる"]),
      ("keyrow",["単体の取得はどちらか",
        "いまの取得は値と指針を組にして返している。"
        "値は Document のもの、指針は Schema のもので、束ねる相手が要る。"
        "<b>「単体の操作はすべて集約のコマンド」とは言い切れない</b>のは、このためである"]),
      ("",["実装の domain/services 24件",
        "仕様に書かれた業務サービスは5件で、19件の開きがある。"
        "この開きが、集約から出された判断なのか本当の業務サービスなのかは、1件ずつ見ないと分からない"]),
    ]))),

 sec("06","答えないこと",
  "他の食い違いと、移す手順は、この決定では扱わない。",
  tbl(["項目","種別","行き先"],[
    ("",["突き合わせのユースケース11件",'<span class="kindtag out">範囲外</span>',
      "<code>uc-check-*</code> は業務ユースケースでない疑いがあるが、集約のコマンドでもない。別に決める"]),
    ("",["24件の個別の判定",'<span class="kindtag out">範囲外</span>',
      "移す作業として別に行う"]),
    ("",["実装をいつ動かすか",'<span class="kindtag out">範囲外</span>',
      "仕様を書いたあとに決める"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">置き換えられた</span><span class="m">2026-08-16 <a href="https://claude.ai/code/artifact/995af0c1-5501-4330-87ea-f456f2684da5">Schema は3つの操作を持つ</a> が置き換えた。判断は引き継がれている</span></div></section>',

 sec("08","関連","この決定は、Schema と Document のコマンドを仕様として書くための前提になる。","",
  fold("縛る対象と、前後の決定を開く（4件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","集約が持つコマンドと、ユースケースが持つ責務"]),
      ("",["引く knowledge",f"{K} ── 呼び出せる操作を持つのは3つ"]),
      ("",["先立つ決定","値オブジェクトとエンティティを、独立して書ける単位にする（承認済み）"]),
      ("",["この決定を使う予定",
        "Schema と Document のコマンドを仕様として書く。"
        "そのとき受け入れ基準と振る舞いの筋書きが、コマンドごとに付く"]),
    ]))),
])

extra2 = extra + """
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
"""
html = ("<title>コマンドを、判断に要るデータのある場所へ戻す</title>"
        f"<style>{CSS}\n{extra2}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-commands-belong-with-data.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")

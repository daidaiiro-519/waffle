import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

# ── 01 いま入っているもの（agg-document の実測）
now = tbl(["ブロック","いま入っているもの","変更後"],[
 ("",["題","文書：agg-document","<b>変えない</b>"]),
 ("",["概要","1文","<b>変えない</b>"]),
 ("keyrow",["集約のルート",
   "名前 <code>Document</code> と、外へ出す相手 <code>Schema</code> の2つだけ",
   "<b>境界の内側</b>（どれがルートか）と<b>境界の外</b>へ分かれる"]),
 ("keyrow",["エンティティ",
   "<b>1件（Document、<code>isRoot: true</code>）。定義そのものが入っている</b> ── 属性23件がここに並ぶ",
   "<b>鍵1つ。</b>定義は <code>ent-document</code> という別の文書へ出る。"
   "<b>ルートも例外にしない</b>"]),
 ("keyrow",["値オブジェクト",
   "<b>5件</b>（DocumentId／DocumentType／DiscriminatorValue／SchemaRef／Status）。"
   "属性と振る舞いの定義もここ",
   "<b>鍵5つ。</b>定義はそれぞれ別の文書へ出る"]),
 ("keyrow",["常に満たすこと","7件。すべて集約が持つ",
   "<b>3件になる。</b>1件がエンティティへ移り、状態に依存する3件が消えるか畳まれる（06）"]),
 ("keyrow",["状態と遷移","状態4・遷移5",
   "<b>持たない。</b>段1 が「導けるものは持たない」と決めており、"
   "適合したか・描いたかは文書と型と成果物から導ける"]),
 ("keyrow",["コマンド","4件。<b>受け入れ基準もシナリオも持たない</b>",
   "<b>欄の名前が「公開する操作」になる。</b>"
   "4件のうち集約を<b>変える</b>ものは1件だけで、"
   "受け入れ基準とシナリオは4件すべてが持つ"]),
 ("",["出す出来事","4件","<b>変えない</b>"]),
 ("keyrow",["不変条件のシナリオ",
   "<b>6件。集約の側に付き</b>、<code>covers</code> で不変条件を指す",
   "<b>コマンドの側へ移す。</b>指し先は不変条件のまま"]),
])

# ── 02 3つの文書
split = tbl(["","集約の文書","エンティティの文書","値オブジェクトの文書"],[
 ("keyrow",["同一性・属性","<b>持たない</b>","<b>持つ</b>","持つ"]),
 ("keyrow",["境界の内側の一覧（どれがルートか）","<b>持つ</b>","持たない","持たない"]),
 ("",["境界の外への参照","<b>持つ</b>","持たない","持たない"]),
 ("",["常に満たすこと","境界をまたぐもの","その型だけで閉じるもの","その値だけで閉じるもの"]),
 ("keyrow",["公開する操作（受け入れ基準・シナリオ付き）","<b>持つ</b>","<b>持たない</b>","持たない"]),
 ("",["常に満たすことを覆う義務","<b>変える操作にだけ掛かる</b>","—","—"]),
 ("",["出す出来事","<b>持つ</b>","持たない","持たない"]),
])

split_why = '<div class="chain">' + "".join([
  step("premise","拠り所",
    "承認済みの筋は「<b>文書のあいだの参照と、実装のオブジェクト参照は別物</b>」である。"
    "何を別の文書にするかは<b>書き方</b>の話で、実装が何を実体で持つかは<b>実装の形</b>の話である"),
  joint("これを当てると"),
  step("conclude","言えること",
    "「集約はエンティティでもある」は<b>実装の形</b>についての言明であり、"
    "<b>文書を何本立てるかを決めない</b>。"
    "ルートを別の文書にしても、実装では集約がそれである ── この2つは両立する"),
  joint("では書き方は何で決めるか"),
  step("evidence","理由",
    "エンティティが<b>ルートかどうかで文書の形が変わらない</b>ほうが、規則が1つ少なくて済む。"
    "境界を引き直したとき ── ルートが内側になる、集約が分かれる ── "
    "<b>動かすのは集約の一覧だけ</b>で、属性23件を文書間で移し替えずに済む"),
  joint("コマンドはどちらへ置くか"),
  step("evidence","出典",
    "書き起こしは「<b>集約が</b>外部へ公開する状態変更メソッドをコマンドと呼ぶ」と、"
    "コマンドを集約に帰している。"
    "実装ではルートのエンティティのメソッドだが、それは実装の形の話である"),
  joint("加えて"),
  step("conclude","言えること",
    "コマンドのシナリオは <code>覆う不変条件</code> で不変条件を指す。"
    "境界をまたぐ不変条件は集約が持つので、"
    "<b>コマンドも集約に置けば、指す先と指す元が同じ文書で閉じる</b>"),
  joint("ただし"),
  step("counter","代償",
    "集約の文書だけを読んでも<b>属性が見えない</b>。1本辿ることになる。"
    "これは値オブジェクトを外へ出したときに受け入れたのと同じ代償である"),
]) + "</div>"

fix = fold("前の版で、ルートを集約に畳んでいた件を開く",
  '<p class="foldnote">この完成イメージの2版目では、「集約はエンティティでもある」を根拠に'
  '<b>ルートを別の文書にしない</b>と書いていた。これは誤りである。'
  '実装の形についての言明を、文書を何本立てるかという書き方の判断へ持ち込んでいた。'
  '<b>置き換えられた決定で犯した混同（文書の参照と実装の参照を1つの言葉で言う）の、'
  'ちょうど裏返しである。</b>'
  '未承認の決定「集約は、自分の境界の内側を持つ」の本文は、当初から'
  '「ルートのエンティティ1つ、内側のエンティティ、内側の値オブジェクト」を'
  '一覧に並べており、決定の側は正しかった。</p>')

# ── 03/04 描いた結果
def kv(k,v): return f'<div class="kv"><span class="k">{k}</span><span class="v">{v}</span></div>'

inside = tbl(["役","単位","指す文書"],[
 ("keyrow",["<b>ルート</b>","エンティティ","<code>ent-document</code>"]),
 ("",["内側","値オブジェクト","<code>vo-document-id</code>"]),
 ("",["内側","値オブジェクト","<code>vo-document-type</code>"]),
 ("",["内側","値オブジェクト","<code>vo-discriminator-value</code>"]),
 ("",["内側","値オブジェクト","<code>vo-schema-ref</code>"]),
 ("",["内側","値オブジェクト","<code>vo-status</code>"]),
 ("",["内側","エンティティ","<b>0件</b> ── この集約は階層を持たない"]),
])

outside = tbl(["相手","指し方"],[
 ("",["<code>agg-schema</code>","<b>識別子で指す。</b>実体は持たない"]),
])

inv_agg = tbl(["規則","担保"],[
 ("",["適合していない文書からは、成果物を描き出せない","検査"]),
 ("",["パス解決は、どの操作からも常にプロジェクトルート内に閉じる","検査"]),
 ("",["schemaRef を持たない文書への schema 解決は、どの操作からも拒否される","検査"]),
])

cmds = tbl(["公開する操作","この集約を変えるか","常に満たすことを覆う義務","受け入れ基準","シナリオ"],[
 ("keyrow",["値を埋める","<b>変える</b>","<b>ある</b>","3件","3件"]),
 ("",["値を取り出す","変えない","無い","2件","2件"]),
 ("",["逸脱していないか判定する","変えない","無い","3件","3件"]),
 ("",["描く","変えない<br><span class='sub'>成果物は書き出す</span>","無い","2件","2件"]),
])

rendered_agg = (
 '<div class="doc">'
 '<div class="idline"><span>id <b>agg-document</b></span>'
 '<span>種別 <b>aggregate</b></span><span>文脈 <b>bc-waffle</b></span></div>'
 '<div class="dt">文書の集約：agg-document</div>'
 '<div class="dp">schema に照らして検証・描画される、構造化された成果物の一貫性単位。</div>'
 '<div class="dh">境界の内側</div>' + inside +
 '<div class="dh">境界の外</div>' + outside +
 '<div class="dh">常に満たすこと（境界をまたぐもの・3件）</div>' + inv_agg +
 '<div class="dh">公開する操作</div>' + cmds +
 '<div class="dh">出す出来事</div>'
 '<div class="dp"><code>DocumentValidated</code>／<code>DocumentRendered</code>／'
 '<code>DocumentDeployed</code>／<code>DocumentSuperseded</code></div>'
 '</div>')

attrs = tbl(["属性","型"],[
 ("keyrow",["<code>documentId</code> <span class='keytag'>同一性</span>",
   "<code>vo-document-id</code>"]),
 ("",["<code>documentType</code>","<code>vo-document-type</code>"]),
 ("",["<code>schemaRef</code>","<code>vo-schema-ref</code>"]),
 ("",["<code>status</code>","<code>vo-status</code>"]),
 ("",["<code>content</code>","構造化データ（schema 準拠）"]),
 ("",["<span class='sub'>ほか18件</span>","<span class='sub'>—</span>"]),
])

inv_ent = tbl(["規則","担保"],[
 ("keyrow",["schemaRef は常に存在する","型"]),
 ("",["documentId は、文書が在るあいだ変わらない","型"]),
])

rendered_ent = (
 '<div class="doc">'
 '<div class="idline"><span>id <b>ent-document</b></span>'
 '<span>種別 <b>entity</b></span><span>文脈 <b>bc-waffle</b></span></div>'
 '<div class="dt">文書：ent-document</div>'
 '<div class="dp">schema に照らして検証・描画される、構造化された成果物。'
 'content が入れ替わり状態が進んでも、同じ文書である。</div>'
 '<div class="dh">同一性 ── 何で同じものと判断するか</div>'
 '<div class="dp"><code>documentId</code>。文書が在るあいだ変わらない。</div>'
 '<div class="dh">属性（23件）</div>' + attrs +
 '<div class="dh">常に満たすこと（この型だけで閉じるもの）</div>' + inv_ent +
 '<div class="cov">どの集約に属するかは、ここには書かない ── '
 '<b><code>agg-document</code> の一覧が、これをルートとして指している</b></div>'
 '</div>')

one_cmd = (
 '<div class="doc">'
 + kv("操作","逸脱していないか判定する")
 + kv("変えるか","<b>変えない</b> ── 呼んだあとも文書は同じである")
 + kv("説明","content が schema に適合するかを判定する。content は書き換えない")
 + '<div class="dh">受け入れ基準</div>'
 '<ul class="dl">'
 '<li>適合しない content を渡したとき、<b>適合しない箇所が返る</b></li>'
 '<li><code>schemaRef</code> を持たない文書を渡したとき、<b>判定せず拒否する</b></li>'
 '<li>判定の前後で content は変わらない</li></ul>'
 '<div class="dh">シナリオ</div>'
 '<pre class="gk">Scenario: schemaRef を持たない文書は判定できない\n'
 '  Given  schemaRef を持たない文書\n'
 '  When   逸脱していないか判定する\n'
 '  Then   拒否され、判定は行われない</pre>'
 '<div class="cov">この操作は集約を変えないので、覆う不変条件を持たない ── '
 '<b>正しさは、この受け入れ基準とシナリオだけが担保する</b></div>'
 '</div>')

# ── 担保のされ方
guard = tbl(["何を","仕様のどこが言うか","実装でどう守るか"],[
 ("keyrow",["<b>変える操作</b>の正しさ","受け入れ基準＋シナリオ",
   "シナリオを実装のテストへ<b>転記して照合する</b>"]),
 ("keyrow",["<b>変えない操作</b>の正しさ","<b>同じ。</b>受け入れ基準＋シナリオ","<b>同じ</b>"]),
 ("",["集約が常に満たすこと","常に満たすこと",
   "<b>変える操作のシナリオが覆う</b>（全体の主張を、変える操作1件ずつへ配る）"]),
 ("",["エンティティ・値オブジェクトが常に満たすこと","常に満たすこと",
   "<b>型で書けないようにする。</b>転記では守れない"]),
])

# ── 06 基準とシナリオ
where = tbl(["何を","どこに付くか","形"],[
 ("keyrow",["<b>受け入れ基準</b>",
   "<b>集約が公開する操作</b>（変える・変えないを問わない）／業務ユースケース／業務サービス ── "
   "<b>呼び出せる操作の側</b>である","「〜のとき、〜となる」"]),
 ("keyrow",["<b>シナリオ</b>","同じ3つ。基準1つにつき少なくとも1つ","Given / When / Then"]),
 ("",["<b>不変条件</b>",
   "<b>集約</b>（境界をまたぐもの）と<b>エンティティ・値オブジェクト</b>（その型だけで閉じるもの）",
   "「常に〜である」"]),
 ("",["集約そのものの受け入れ基準","<b>持たない</b>","—"]),
 ("",["エンティティ・値オブジェクトの受け入れ基準","<b>持たない。</b>不変条件だけを持つ","—"]),
])

why = '<div class="chain">' + "".join([
  step("premise","前提",
    "受け入れ基準と振る舞いは、要素そのものにではなく、"
    "<b>要素が公開する呼び出せる操作</b>に付く。"
    "持つのは業務ユースケース・業務サービス・集約のコマンドの3つである"),
  joint("だから"),
  step("conclude","言えること",
    "集約は呼び出せる操作を<b>公開する操作として持つ</b>ので、"
    "受け入れ基準とシナリオは操作1つ1つに付く。"
    "<b>集約そのものには付かない</b>"),
  joint("では不変条件はどうなるか"),
  step("premise","前提",
    "不変条件は「<b>あらゆる操作列のあとで成り立つ</b>」という全称の主張であり、"
    "個別の基準を集めても表せない"),
  joint("ただし"),
  step("evidence","出典",
    "書き起こしは「状態を変更できるのは集約内部の業務ロジックだけ」"
    "「内部の他のエンティティの状態を変えるコマンドも、必ずルートを経由して実行する」と定める"),
  joint("だから"),
  step("conclude","言えること",
    "状態を変える経路が<b>宣言済みのコマンドだけに閉じている</b>なら、"
    "「あらゆる操作列」は有限のコマンド集合に閉じる。"
    "全称は<b>各コマンドの個別命題へ分配できる</b>"),
  joint("ここで効くのが操作の分けかたである"),
  step("conclude","言えること",
    "<b>集約を変えない操作は、常に満たすことを破りようがない</b>。"
    "だから覆う義務が掛かるのは<b>変える操作だけ</b>である。"
    "外へ書き出すかどうかではなく、<b>この集約が変わるか</b>が境目になる ── "
    "<code>描く</code> は成果物を書き出すが、文書は変わらないので義務が無い"),
  joint("結果として"),
  step("conclude","結論",
    "常に満たすことは<b>集約とエンティティが持ったまま</b>。"
    "それを覆うシナリオは<b>変える操作の側</b>に置き、"
    "<code>覆う不変条件</code> で指す。指し先は文書をまたいでよい"),
  joint("ただし"),
  step("counter","代償",
    "書く量は<b>変える操作の数 × 常に満たすことの数</b>で効く。"
    "文書の集約は操作4件・3件だが、"
    "<b>変えるものは1件だけなので 1 × 3 に収まる</b>。"
    "階層を持つ集約では変える操作が増え、この掛け算が大きくなる ── "
    "<b>大きすぎることが、集約が大きすぎる合図になる</b>"),
]) + "</div>"

names = tbl(["いまの欄の名前","付く場所","変更後"],[
 ("keyrow",["<code>invariantScenarios</code>","集約","<b>シナリオ</b>（操作の中）"]),
 ("keyrow",["<code>acceptanceScenarios</code>","ユースケース／業務サービス","<b>シナリオ</b>"]),
 ("",["<code>acceptanceCriteria</code>","ユースケース／業務サービス","<b>受け入れ基準</b>"]),
 ("",["（操作には無い）","—","<b>受け入れ基準・シナリオを持たせる</b>"]),
 ("keyrow",["<code>commands</code>","集約","<b>公開する操作</b>。"
   "変えるかどうかは「<b>この集約を変えるか</b>」の欄が示す"]),
])

names_note = ('<p class="foldnote">「コマンド」を表に出さない理由 ── '
 '書き起こしは<b>「技術的な説明は業務エキスパートに伝わらず、業務ロジックの正しい理解を妨げる」</b>と述べる。'
 'コマンド・エンティティ・値オブジェクト・集約は<b>設計する人どうしの言葉</b>であって、'
 '事業活動を表す言葉ではない。'
 'いっぽう<b>「この操作を呼ぶと、この文書は変わるのか」は業務の人が即答できる</b>。'
 '<b>伝わらないのは名前だけで、区別そのものではない。</b>'
 'だから区別は残し、名前を業務の言葉にする。'
 '「変えるものを、ドメイン駆動設計ではコマンドと呼ぶ」は<b>書く指針の中だけ</b>に置き、'
 '文書の表面には出さない。'
 'これは <code>create</code>／<code>validate</code>／<code>render</code> を'
 '「値を埋める／逸脱していないか判定する／描く」へ変えた判断、'
 'および図の関係を記号でなく言葉で書くと決めた判断と同じ形である。</p>')

counts = tbl(["集約","ルートのエンティティ","内側のエンティティ","値オブジェクト"],[
 ("keyrow",["<code>agg-document</code>","<code>ent-document</code>","<b>0件</b>","5件"]),
 ("keyrow",["<code>agg-schema</code>","<code>ent-schema</code>","<b>0件</b>","5件"]),
 ("",["<b>合計</b>","<b>2本</b>","<b>0本</b>","<b>10本</b>"]),
])

body = "".join([
 '<header><p class="eyebrow">完成イメージ</p>'
 '<h1>集約の文書は、こうなる</h1>'
 '<p class="lede">エンティティと値オブジェクトは、'
 '<b>ルートかどうかによらず全部が別の文書</b>になる。'
 '集約の文書に残るのは<b>境界</b>である ── '
 'どれが内側でどれがルートか、境界をまたぐ不変条件、公開する操作。'
 '受け入れ基準とシナリオは<b>操作1つ1つ</b>に付く。'
 '実例は、いま実在する <code>agg-document</code> を使う。'
 '<b>この頁は bc-waffle だけを見ている。</b></p></header>',

 sec("01","いま何が入っていて、何が変わるか",
  "変わるのは<b>5ブロック</b>である。定義を抱えていた2つが鍵になり、"
  "状態と遷移が消え、不変条件が振り分けられ、"
  "コマンドの欄が「公開する操作」になって受け入れ基準とシナリオを持つ。",
  now,
  fold("測り方を開く",
    '<p class="foldnote"><code>.waffle/documents/specs/bc-waffle/aggregate/agg-document.json</code> を'
    'ブロックごとに数えた ── エンティティ<b>1件</b>（<code>isRoot: true</code>、属性23件）、'
    '値オブジェクト5件、不変条件7件、状態4・遷移5、コマンド4件、出す出来事4件、'
    '不変条件のシナリオ6件。'
    '<b>コマンドが持つ欄は名前・説明・要る状態・後の状態・入力・出す出来事の6つで、'
    '受け入れ基準もシナリオも無い。</b></p>')),

 sec("02","3つの文書が、それぞれ何を持つか",
  "<b>ルートも例外にしない。</b>エンティティは、ルートかどうかで文書の形が変わらない。"
  "ルートであることを言うのは<b>集約の側</b>である。",
  split + fix,
  fold("なぜそうするかを開く", '<div style="padding:.9rem">'+split_why+'</div>')),

 sec("03","描いた結果 ── 集約の文書",
  "属性は消えるのではなく、<b>エンティティの文書へ出て鍵で指される</b>。"
  "集約の文書を読めば、境界がどこまでかが1か所で分かる。",
  rendered_agg),

 sec("04","描いた結果 ── エンティティの文書",
  "属性23件はここへ来る。不変条件は<b>この型だけで閉じるもの</b>だけを持ち、"
  "残る6件は集約に置いたままにする。",
  rendered_ent),

 sec("05","操作1件を開くと",
  "<b>集約を変えない操作も、受け入れ基準とシナリオを持つ。</b>"
  "変えないことで外れるのは<b>常に満たすことを覆う義務だけ</b>である。",
  one_cmd + '<h3 class="sub-h">担保のされ方</h3>' + guard),

 sec("06","受け入れ基準とシナリオは、どこに付くか",
  "<b>集約そのものには付かない。</b>付くのは呼び出せる操作の側である。"
  "不変条件を覆うのは<b>集約を変える操作</b>のシナリオである。",
  where, fold("なぜそうなるかを開く", '<div style="padding:.9rem">'+why+'</div>')),

 sec("07","文書の表面に、技術の語を出さない",
  "同じものが3つの名前で呼ばれている件と、"
  "<b>技術の語が表に出ている件</b>を、まとめて直す。",
  names, fold("「コマンド」を表に出さない理由を開く", names_note)),

 sec("08","この文脈で、何本の文書が増えるか",
  "bc-waffle の集約2本から、<b>エンティティ2本と値オブジェクト10本</b>が出る。"
  "どちらの集約も<b>階層を持たない</b>ので、内側のエンティティは1本も出ない。"
  "不変条件19件を「その型ひとつを見れば足りるか」で通すと、<b>4件が動いた</b> ── "
  "<code>agg-document</code> から1件がエンティティへ、"
  "<code>agg-schema</code> から3件が図の宣言の値オブジェクトへ。",
  counts,
  fold("測り方を開く",
    '<p class="foldnote">bc-waffle の集約2本の <code>entities</code> を '
    '<code>isRoot</code> で数えた ── どちらもルート1件のみで、内側のエンティティは0件。'
    '値オブジェクトは <code>agg-document</code> が5件'
    '（DocumentId／DocumentType／DiscriminatorValue／SchemaRef／Status）、'
    '<code>agg-schema</code> が5件'
    '（SchemaId／Version／KindProfile／DiscriminatorKey／FigureDeclaration）。'
    '<b>集約の名前は2本ともルートの名前と一致していた。</b></p>')),

 sec("09","まだ決めていないこと",
  "残るのは3点。<b>新しい判断が要るのは1点だけ</b>で、"
  "残る2点は直す先が決まっている。",
  tbl(["項目","いまの状態","行き先"],[
   ("keyrow",["変える操作に、変える相手を書かせるか",
     "<b>唯一、新しい判断が要るもの。</b>"
     "bc-waffle の集約はどちらも階層を持たないので実物が答えを持たず、"
     "書き起こしも「ルートを経由する」としか言わない",
     "<b>書けるようにする</b>ことを推す。書けないと階層を持つ集約を表せず、"
     "使わない文脈では空のままで害が無い"]),
   ("",["受け入れ基準を持つのは「集約のコマンド」という knowledge の一節",
     "コマンドを状態変更に絞ったので、"
     "<b>変えない操作の受け入れ基準が宙に浮く</b>",
     "<code>operation-contract-closes-invariants</code> の当該節を"
     "「集約が公開する操作」へ直す"]),
   ("",["<code>agg-document</code> の操作が古い",
     "<b>いまは create／validate／render／supersede</b> のまま。"
     "承認済みの4つ（値を埋める／値を取り出す／逸脱していないか判定する／描く）と食い違っている",
     "移す作業で直す。この完成イメージでは承認済みの4つで描いている"]),
  ])),
])

extra2 = extra + """
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
.doc{border:1px solid var(--rule);border-radius:2px;background:var(--surface);padding:1.1rem 1.2rem;
     display:flex;flex-direction:column;gap:.8rem}
.doc .scroll{background:var(--surface-2)}
.idline{display:flex;flex-wrap:wrap;gap:1.2rem;font-family:var(--mono);font-size:.7rem;
        color:var(--ink-faint);padding-bottom:.6rem;border-bottom:1px solid var(--rule-soft)}
.dt{font-family:var(--serif);font-size:1.15rem;font-weight:600}
.dp{font-size:.9rem;line-height:1.8;color:var(--ink-soft)}
.dp b{color:var(--ink)}
.dh{font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-faint);margin-top:.3rem}
.dl{margin:0;padding-left:1.2rem;font-size:.9rem;line-height:1.85;color:var(--ink-soft)}
.dl b{color:var(--ink)}
.gk{margin:0;font-family:var(--mono);font-size:.8rem;line-height:1.8;background:var(--surface-2);
    border:1px solid var(--rule-soft);border-radius:2px;padding:.7rem .9rem;overflow-x:auto}
.cov{font-size:.84rem;color:var(--ink-soft);padding-left:.8rem;border-left:2px solid var(--infer)}
.kv{display:flex;gap:.8rem;align-items:baseline;flex-wrap:wrap}
.kv .k{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
       color:var(--ink-faint);flex:none;min-width:5rem}
.kv .v{font-size:.95rem;line-height:1.75}
"""
html = ("<title>集約の文書は、こうなる</title>"
        f"<style>{CSS}\n{extra2}</style>"
        f'<div class="wrap">{body}</div>')
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/aggregate-doc-preview.html").write_text(html, encoding="utf-8")
print("書いた", len(html), "bytes")

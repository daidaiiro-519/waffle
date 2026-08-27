import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra

FF='font-family="Noto Sans JP, Hiragino Kaku Gothic ProN, Yu Gothic, sans-serif"'
DEFS=('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-faint)"/></marker></defs>')
def gb(x,y,w,h,t,s=None,a="var(--rule)",strong=False):
    o=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="var(--surface)" stroke="{a}" stroke-width="{2 if strong else 1}"/>'
    o+=f'<text x="{x+w/2}" y="{y+(h/2+5 if not s else h/2-3)}" text-anchor="middle" font-size="13.5" font-weight="600" fill="var(--ink)">{t}</text>'
    if s: o+=f'<text x="{x+w/2}" y="{y+h/2+16}" text-anchor="middle" font-size="11" fill="var(--ink-faint)">{s}</text>'
    return o
def ga(x1,y1,x2,y2,lb=None,lx=None,ly=None):
    o=f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--ink-faint)" stroke-width="1.4" marker-end="url(#ah)"/>'
    if lb: o+=(f'<text x="{lx or (x1+x2)/2}" y="{ly or (y1+y2)/2}" text-anchor="middle" font-size="11" '
               f'fill="var(--ink-faint)">{lb}</text>')
    return o
def gsvg(vb,inner,cap):
    return (f'<figure class="fig"><div class="scroll"><svg viewBox="{vb}" role="img" '
            f'style="min-width:44rem;width:100%;height:auto;display:block" {FF}>{DEFS}{inner}</svg></div>'
            f'<figcaption>{cap}</figcaption></figure>')

a=''
a+='<text x="12" y="20" font-size="11.5" fill="var(--against)">変更前 ── 書き手が描き方を選ぶので、同じ意味に名前が2つできる</text>'
a+=gb(12,32,206,54,"書き手","描き方を選ぶ","var(--against)",True)
a+=ga(218,59,300,59)
a+=gb(300,32,232,54,"kvtable / keyvalue","同じ意味、違う描き方","var(--against)")
a+=ga(532,59,614,59)
a+=gb(614,32,160,54,"Markdown")
a+='<text x="12" y="140" font-size="11.5" fill="var(--infer)">変更後 ── 書き手は意味を書き、描き方は描き先ごとに決まる</text>'
a+=gb(12,152,206,54,"書き手","意味を書く","var(--infer)",True)
a+=ga(218,179,300,179)
a+=gb(300,152,232,54,"名前と値の組","意味の名前ひとつ","var(--infer)")
a+=ga(532,166,614,138,"Markdown なら箇条",560,124)
a+=ga(532,192,614,220,"HTML なら表",556,238)
a+=gb(614,112,160,52,"箇条として描く")
a+=gb(614,196,160,52,"表として描く")
FIG1=gsvg("0 0 790 262",a,
 "<b>同じ意味に名前が2つあるのは、書き手に描き方を選ばせているからである。</b>"
 "意味をひとつにすれば、描き分けは描き先ごとに決まる。")

b=''
b+='<rect x="16" y="28" width="250" height="186" rx="4" fill="none" stroke="var(--assume)" stroke-width="1" stroke-dasharray="4 3"/>'
b+='<text x="24" y="22" font-size="11" fill="var(--assume)">構造の部品 ── 自分では何も描かない</text>'
b+=gb(34,46,214,46,"見出しを付けて繰り返す","section","var(--assume)")
b+=gb(34,104,214,46,"入れ子の中を描く","object","var(--assume)")
b+=gb(34,162,214,46,"変更前と変更後を並べる","足りていない","var(--assume)",True)
b+='<rect x="300" y="28" width="250" height="186" rx="4" fill="none" stroke="var(--infer)" stroke-width="1" stroke-dasharray="4 3"/>'
b+='<text x="308" y="22" font-size="11" fill="var(--infer)">意味 ── 何を述べるか</text>'
b+=gb(318,46,214,46,"文 / 並び / 表 / コード",None,"var(--infer)")
b+=gb(318,104,214,46,"名前と値の組",None,"var(--infer)")
b+=gb(318,162,214,46,"図の主張 16種",None,"var(--infer)")
b+='<rect x="584" y="28" width="250" height="186" rx="4" fill="none" stroke="var(--fact)" stroke-width="1" stroke-dasharray="4 3"/>'
b+='<text x="592" y="22" font-size="11" fill="var(--fact)">共通の欄 ── どの部品にも付く</text>'
b+=gb(602,46,214,46,"値の取り出し元","from","var(--fact)")
b+=gb(602,104,214,46,"見出し / 空のときの文言",None,"var(--fact)")
b+=gb(602,162,214,46,"読む必要の度合い","のちに落とした","var(--fact)")
FIG2=gsvg("0 0 850 228",b,
 "いまは3つが同じ並びに置かれている。<b>分けると、足りていないものが見える</b>——"
 "この時点では2つ見えた。<b>うち読む必要の度合いは、のちに持たないと決着した</b>——"
 "索引は部品の鍵と説明から導けるため。残るのは<b>変更前と変更後を並べる部品の1つ</b>。")

vocab = tbl(["群","変更前","変更後"],[
 ("keyrow",["<b>構造の部品</b><br><span class='sub'>中身を描かず、並べ方だけを決める</span>",
   "<code>section</code> / <code>object</code> が、意味の部品と同じ並びにある",
   "<b>分ける。</b>見出しを付けて繰り返す（<code>section</code>）／入れ子の中を描く（<code>object</code>）／<b>変更前と変更後を並べる（足す）</b>"]),
 ("keyrow",["<b>意味の部品</b><br><span class='sub'>文字</span>",
   "<code>paragraph</code> / <code>list</code> / <code>table</code> / "
   "<code>kvtable</code> / <code>keyvalue</code> / <code>code</code>",
   "<b>4つ。</b>文（<code>paragraph</code>）／並び（<code>list</code>）／表（<code>table</code>）／コード（<code>code</code>）。<b><code>kvtable</code> と <code>keyvalue</code> は1つにまとめる</b>（名前と値の組）"]),
 ("",["<b>意味の部品</b><br><span class='sub'>図</span>",
   "描き方の名前16（<code>flowchart</code> ほか5種は Mermaid 由来）",
   "<b>16の主張から1つ選んで書く</b>（関係7・量9）。<b>一部は囲み（<code>frame</code>）と線（<code>links</code>）の設定から導ける</b>ので、名前として残すかは仕様で決める"]),
 ("",["<b>共通の欄</b>",
   "<code>from</code> / <code>heading</code> / <code>emptyText</code> が部品ごとの欄と混ざる",
   "<b>分ける。</b>値の取り出し元（<code>from</code>）／見出し（<code>heading</code>）／空のときの文言（<code>emptyText</code>）。<b>~~読む必要の度合い~~</b> は<b>のちに持たないと決着</b>"]),
 ("",["<b>落とすもの</b>","<code>divider</code>（使用0）","<b>落とす。</b>区切り線は意味を持たない"]),
])

lack = tbl(["足りないもの","何を述べる語か","いま何が起きているか"],[
 ("keyrow",["変更前と変更後を並べる部品","変更前と変更後を並べ、何が変わったかを見せる",
   "<b><code>対応</code> が肩代わりしている。</b>表の交差を述べる主張と、並べる部品を兼ねている"]),
 ("",["~~読む必要の度合い~~","本筋か、裏付けか、内訳か",
   "<b>のちに持たないと決着した。</b>索引は部品の鍵と説明から導けるので、項目ごとに申告させる必要が無い"]),
 ("",["囲み（<code>frame.groups</code>）","並びや点と線の一部に、名前つきの囲みを掛ける",
   "実例で使われ、<b>「書けない」という注記が残っている</b>"]),
 ("",["差分の語彙","変わっていない／注目／足した／落とした／変えた",
   "決定で定めたのに、<code>role</code> は "
   "<code>plain</code>/<code>focus</code>/<code>muted</code>/<code>start</code>/<code>end</code> のまま"]),
])

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">同じ意味に名前がひとつ<br><span class="sub">決め手</span></th>
<th>Markdown で描けることが下限になる</th>
<th>足りない語が見える</th>
<th>いまの schema を書き換えずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">意味の名前だけにし、構造の部品と共通の欄を分ける<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">いまのまま置く</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">重複した名前だけをまとめる</td><td>{ok}</td><td>{ng}</td><td>{ng}</td><td>{ng}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く ── なぜその条件が要るか、なぜ × なのか（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['同じ意味に名前がひとつ<span class="keytag">決め手</span>',
      "名前が2つあると、書き手はどちらかを選ぶことになる。"
      "選ばせている以上それは描き方であって、意味ではない",
      "<b>いまのまま</b> <code>kvtable</code> と <code>keyvalue</code> は同じ <code>_table</code> 相当の意味を持ちながら、"
      "表と箇条という2つの描き方で分かれている"]),
    ("",["Markdown で描けることが下限になる",
      "描き先が増えても語彙が変わらないようにするには、最も表現力の低い描き先で描けることが要る",
      "<b>いまのまま</b>／<b>名前だけまとめる</b> ── どちらも <code>x-frontmatter</code> のような "
      "Markdown 専用の語が残る"]),
    ("",["足りない語が見える",
      "構造・意味・共通の欄が同じ並びにあると、どの群に何が足りないかを問えない",
      "<b>いまのまま</b>／<b>名前だけまとめる</b> ── 群が分かれないので、"
      "変更前と変更後を並べる部品と読む必要の度合いが欠けていることが現れない"]),
    ("",["いまの schema を書き換えずに済む",
      "書き換える範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>採る案</b>／<b>名前だけまとめる</b> ── どちらも書き換える"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("evidence","測った",
    "<code>kvtable</code> と <code>keyvalue</code> は、<b>どちらも「1つのものの、名前と値の組」を描いている</b>。"
    "違うのは表にするか箇条にするかだけである"),
  joint("図の側も同じだった"),
  step("evidence","測った",
    "図の5種（<code>flowchart</code>・<code>sequence</code>・<code>statediagram</code>・"
    "<code>architecture</code>・<code>graph</code>）は Mermaid 由来の描き方の名前で、"
    "<b>描き方ごとに違う欄が生えている</b>"),
  joint("だから"),
  step("conclude","言えること",
    "<b>文字の側も図の側も、書き手に描き方を選ばせている。</b>"
    "図についてだけ主張の名前へ移す決定を済ませたが、同じことが文字の側に残っている"),
  joint("並びを見ると"),
  step("evidence","測った",
    "<code>section</code> と <code>object</code> は<b>自分では何も描かない</b>。"
    "<code>object</code> は入れ子の中を描くだけである。"
    "また <code>from</code>・<code>heading</code>・<code>emptyText</code> は<b>どの部品にも付く</b>"),
  joint("だから"),
  step("conclude","言えること",
    "構造の部品と、共通の欄と、意味の部品が<b>同じ並びに置かれている</b>"),
  joint("分けて数え直すと"),
  step("evidence","測った",
    "<b>2つ足りない。</b>変更前と変更後を並べる部品（いまは <code>対応</code> が肩代わり）と、"
    "読む必要の度合い。<b>後者はのちに持たないと決着した</b>ので、いま足りないのは<b>その部品の1つ</b>である"),
  joint("合わせると"),
  step("conclude","結論",
    "語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける。"
    "描き方は宣言から外し、意味と描き先から決まるようにする"),
  joint("なお"),
  step("premise","前提",
    "<b>Markdown で描けることが語彙の下限になる。</b>"
    "HTML の方が豊かに描けるが、それは同じ意味をより良く描けるということであって、"
    "HTML でしか言えない意味があるということではない"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（5件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["<code>kvtable</code> と <code>keyvalue</code> が同じ意味",
      '<span class="kindtag unv">実測</span>',
      "描く実装の分岐を読んだ。一方は表の1行、他方は箇条として同じ組を描く","—"]),
    ("",["図の5種が描き方の名前",'<span class="kindtag unv">実測</span>',
      "属性が <code>transitionsFrom</code>・<code>participantsFrom</code>・"
      "<code>nodesFrom</code>・<code>connectionsFrom</code> と描き方ごとに違う","—"]),
    ("",["構造の部品が何も描かない",'<span class="kindtag unv">実測</span>',
      "<code>object</code> は入れ子の中を描くだけ、<code>section</code> は見出しを立てて <code>each</code> を描く","—"]),
    ("",["2つ足りない",'<span class="kindtag unv">実測</span>',
      "変更前後の図が <code>対応</code> で書かれている実例と、"
      "この決定の折りたたみが宣言から出ていないこと","—"]),
    ("",["Markdown が下限になる",'<span class="kindtag out">Waffle の設計判断</span>',
      "<b>knowledge に該当なし</b>",
      "<b>HTML でしか言えない意味が1つでも出てきたとき</b>"]),
  ])
  + '<p class="foldnote">最後の段だけ裏付けが実測でない理由 ── '
    'これは測って分かることではなく、どこを下限に置くかという選び方である。'
    '崩れるときも書いてある。</p>')

body = "".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける</h1>'
 '<p class="lede"><code>kvtable</code> と <code>keyvalue</code> は、どちらも「1つのものの、名前と値の組」を描く。'
 '違うのは表にするか箇条にするかだけである。'
 '<b>書き手に描き方を選ばせている。</b>図についてだけ直したものが、文字の側に残っている。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>描く語彙を意味の名前だけにする</b>。'
  '構造の部品と共通の欄は、意味の部品から分けて置く。'
  '描き方は宣言から外し、意味と描き先から決まるようにする。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt"><b>同じ意味に名前が2つあるなら、それは描き方である。</b>'
  '書き手が選んでいる以上、選ばれているのは意味ではない。'
  '<code>kvtable</code> と <code>keyvalue</code>、'
  '<code>graph</code> と <code>flowchart</code> が、どちらもその形になっている。</span></div></div>'),

 sec("02","変更前と変更後",
  "変わるのは<b>誰が描き方を決めるか</b>である。書き手は意味だけを書く。",
  FIG1 + '<h3 class="sub-h">語彙で見る</h3>' + vocab +
  '<h3 class="sub-h">分けると、足りていないものが見える</h3>' + FIG2 + lack),

 sec("03","理由",
  "文字の側も図の側も、書き手に描き方を選ばせている。"
  "<b>構造の部品と共通の欄が、意味の部品と同じ並びに置かれている。</b>",
  reason, reason_fold),

 sec("04","判断を分けた軸",
  "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>いまの schema を書き換えることになる</b>。",
  axis, axis_fold),

 sec("05","付随して決めたこと",
  "語彙を意味へ寄せると、いくつかの名前の行き先が決まる。3点を同時に決めた。",
  tbl(["論点","決定"],[
    ("keyrow",["<code>対応</code> の2つの顔",
      "<b>表の縦横が交わる主張だけに戻す。</b>変更前と変更後を並べる役目は、別の部品として立てる"]),
    ("",["<code>divider</code>","<b>落とす。</b>使用0で、区切り線は意味を持たない"]),
    ("",["描き先ごとの表現力の差",
      "<b>描き手が吸収する。</b>「裏付け」は HTML では折りたたんで、Markdown では小見出しで描く"]),
  ]),
  fold("それぞれの根拠を開く（3件）",
    tbl(["論点","根拠"],[
      ("keyrow",["<code>対応</code> の2つの顔",
        "実例では、<b>表の縦横が交わる主張</b>（仕様の要素 × 実装で確かめるもの）と、"
        "<b>図を2つ並べる部品</b>（変更前 × 変更後）の両方に使われている。"
        "<b><b>その部品の名前が無いので肩代わりしている</b></b>"]),
      ("",["<code>divider</code>",
        "最新版の schema で使用0。描く実装には分岐があるが、"
        "宣言する相手がいない。<b>区切り線は描き方であって意味ではない</b>"]),
      ("keyrow",["描き先ごとの表現力の差",
        "折りたたみは意味ではなく描き方である。意味は「裏付け」「内訳」「根拠」で、"
        "この決定の折りたたみの見出しがそれを言っている。"
        "<b>HTML が豊かなのは同じ意味をより良く描けるということ</b>であり、"
        "HTML でしか言えない意味があるということではない"]),
    ]))),

 sec("06","答えないこと",
  "名前と欄の形は仕様で決める。この決定は<b>群の分け方と、描き方を宣言から外すこと</b>だけを定める。",
  tbl(["項目","何が決まっていないか","いつ決めるか","どこで決まるか"],[
    ("keyrow",["各語の名前","文／並び／表／コード／名前と値の組 は仮に置いたもの",
      "<b>仕様を書くとき</b>","<b>仕様そのもの。</b>決定にはしない"]),
    ("keyrow",["<b>読む必要の度合いの段階</b>",
   "<b>持たないことに決着した。</b>索引は部品の鍵と説明から導ける",
   "<b>決着（2026-08-16）</b>","段1 の仕様"]),
    ("",["導けるものを名前として残すか",
      "囲みと線の設定から導ける主張を、名前として残すか消すか。<b>何個が導けるかも、そこで数える</b>",
      "<b>仕様を書くとき</b>","同上。導けることと、読み手に見せることは別"]),
    ("",["移す順序","いまの schema と既存の Document をどう移すか",
      "<b>仕様の合意後、実装の前</b>","移す計画"]),
  ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-15</span></div></section>',

 sec("08","関連","この決定は、図についての2つの決定を文字の側へ広げるものである。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","描く語彙の名前と、その群分け"]),
      ("",["先立つ決定","図の語彙を、描き方の名前から主張の名前へ移す（承認済み）"]),
      ("",["先立つ決定","図の宣言を、主張を軸にした形へ置き換える（承認済み）"]),
      ("",["先立つ決定","Schema を仕様から実装し、型は Document として置く（承認済み）── "
        "この語彙は段1 が持つ"]),
      ("",["この決定を使う予定",
        "語彙の再定義を仕様として書く。各語の名前・書ける場所・"
        "描き先ごとの落とし方を並べる"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
.sub-h{font-family:var(--serif);font-size:1rem;font-weight:600;margin:.5rem 0 -.3rem;color:var(--ink-soft)}
"""
html=("<title>語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける</title>"
      f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-vocabulary-by-meaning.html").write_text(html,encoding="utf-8")
print("書いた",len(html))

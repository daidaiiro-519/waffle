import sys, pathlib
sys.path.insert(0,"/home/daidaiiro/workspace/waffle/docs/adr/build")
from _common import CSS, sec, fold, tbl, step, joint, ok, ng, extra
C=lambda s: f"<code>{s}</code>"
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
a+='<text x="14" y="18" font-size="11" fill="var(--against)">変更前 ── 型ごとに、同じ概念へ自分の名前を付ける</text>'
a+=gb(14,30,140,40,"specKind",None,"var(--against)")
a+=gb(164,30,140,40,"codingKind",None,"var(--against)")
a+=gb(314,30,140,40,"skillKind ほか3つ",None,"var(--against)")
a+=gb(14,80,440,36,"UsecaseContent ／ AggregateContent ／ …34個",None,"var(--against)")
a+='<text x="14" y="148" font-size="11" fill="var(--infer)">変更後 ── 段1 が概念を1つ提供し、段2 は枝を並べるだけ</text>'
a+=gb(14,160,180,44,"種別","段1 の部品ひとつ","var(--infer)",True)
a+=ga(194,182,262,182)
a+=gb(262,160,290,44,"枝ごとの必須ブロックの一覧","名前つきの入れ物は要らない","var(--infer)")
FIG=gsvg("0 0 580 220",a,
 "<b>同じ概念に、型ごとの名前が付いていた。</b>"
 "鍵と説明で直したのと同じ形である。覆うのではなく、落とす。")

parts1 = tbl(["群","部品","落ちる先"],[
 ("keyrow",["<b>表紙</b>","識別子／型と版／種別／状態／役どころ／時刻／ラベル",
   "固定の欄と必須"]),
 ("keyrow",["<b>構造の文法</b>","値／まとまり／<b>並び</b>／入れ子／選び／名前で共有 ── <b>6つ</b>",
   f"{C('type')}／{C('properties')}／{C('items')}／展開／{C('allOf')}+{C('if')}/{C('then')}／{C('$defs')}+{C('$ref')}"]),
 ("",["<b>修飾</b>","必須／決め打ち／選択肢／最小の個数／閉じる／<b>既定値</b> ── 6つ",
   f"{C('required')}／{C('const')}／{C('enum')}／{C('minItems')}／{C('additionalProperties')}／{C('default')}"]),
 ("keyrow",["<b>標準の組み立て</b>","<b>図・木</b>","段1 が名前付きで持つ"]),
 ("",["<b>意味の語</b>","記入の指針／読み方","欄とブロックに付く"]),
 ("",["<b>描き方の語</b>","描き方／成果物の宛先 ── <b>6語から2語へ</b>","ブロックと型の根に付く"]),
])

parts2 = tbl(["段2 が宣言すること","段1 のどの部品で組むか"],[
 ("",["<b>1</b> 型の名前と版","値"]),
 ("keyrow",["<b>2</b> 種別 ── どの欄が種別で、どんな枝があるか","選び＋選択肢"]),
 ("keyrow",["<b>3</b> ブロックの定義 ── 名前・中身の形・必須か","まとまり／並び／入れ子＋修飾"]),
 ("keyrow",["<b>4</b> 枝ごとの必須ブロック","選び"]),
 ("",["<b>5</b> 共有する組み立て","名前で共有"]),
 ("",["<b>6</b> 各所の指針","意味の語"]),
 ("",["<b>7</b> 描き方","描き方の語"]),
 ("",["<b>8</b> 成果物の宛先","宛先の語"]),
])

waste = tbl(["実物にある無駄","実測","賄わない理由"],[
 ("keyrow",["<b>種別の鍵が6つある</b>",
   f"{C('specKind')}／{C('codingKind')}／{C('skillKind')}／{C('agentKind')}／{C('templateKind')}／{C('hookKind')}",
   "<b>どれも同じ概念。</b>型ごとに自分の名前を付けているだけで、1つでよい"]),
 ("keyrow",["<b>枝ごとに名前つきの中身がある</b>",
   f"{C('UsecaseContent')} ほか<b>34個</b>",
   "枝が言うべきなのは「この枝ではこれらのブロックが要る」だけ。<b>名前つきの入れ物は要らない</b>"]),
 ("",[C("pattern")+" を制限として数えていた","1件",
   "<b>正規表現としては一度も使われていない。</b>偶然そういう名前の欄だった"]),
])

axis = f'''<div class="scroll"><table>
<thead><tr><th>案</th>
<th class="keycol">段2 が部品だけで組める<br><span class="sub">決め手</span></th>
<th>同じ概念に名前が1つ</th><th>落とし方が一意に決まる</th><th>いまの型を書き換えずに済む</th></tr></thead>
<tbody>
<tr class="pickrow"><td class="cond">段1 が部品を提供し、段2 が8つを宣言する<br><span class="sub">採る</span></td>
<td>{ok}</td><td>{ok}</td><td>{ok}</td><td>{ng}</td></tr>
<tr><td class="cond">いまの形を語彙として認める</td><td>{ng}</td><td>{ng}</td><td>{ng}</td><td>{ok}</td></tr>
<tr><td class="cond">JSON Schema をそのまま宣言に使い続ける</td><td>{ng}</td><td>{ng}</td><td>{ok}</td><td>{ok}</td></tr>
</tbody></table></div>'''

axis_fold = fold("条件の内訳を開く（4件）",
  tbl(["条件（全文）","なぜこの条件が要るか","× の理由"],[
    ("keyrow",['段2 が部品だけで組める<span class="keytag">決め手</span>',
      "<b>段2 が自前で部品を作っていたら、それは段1 の欠落である。</b>"
      "部品で足りれば、欠落が無いと言える",
      "<b>いまの形を認める</b> 図と木が段2 で自前に組まれたまま残る<br>"
      "<b>JSON Schema のまま</b> 同じ"]),
    ("",["同じ概念に名前が1つ",
      "名前が複数あると、書き手はどれかを選ぶ。選ばせている以上それは概念ではない",
      "<b>いまの形を認める</b> 種別の鍵が6つ残る<br>"
      "<b>JSON Schema のまま</b> 同じ"]),
    ("",["落とし方が一意に決まる",
      "部品ひとつに行き先が1つ対応しないと、型を起こす規則が書けない",
      "<b>いまの形を認める</b> 同じ概念に複数の書き方が残るので、規則が分岐する"]),
    ("",["いまの型を書き換えずに済む",
      "書き換える範囲が広いほど、途中で止まったときに新旧が混ざる",
      "<b>採る案</b> 型10本を書き直す"]),
  ]))

reason = '<div class="chain">' + "".join([
  step("premise","前提",
    "<b>段1 はこのスキーマが表現できる部品を全て提供し、段2 はそれを組み合わせて表現する。</b>"
    "数えなくても判定でき、型が1本増えても答えが変わらない"),
  joint("この基準を当てると"),
  step("evidence","測った",
    "<b>段2 が自前で部品を組んでいる箇所がある。</b>"
    f"{C('KnowledgeSchema')} の図と概念の木、{C('SkillSchema')} の手順の親子 ── "
    "<b>2つの型が、同じ「深さ有界の木」を別々の名前で組んでいた</b>"),
  joint("だから"),
  step("conclude","言えること",
    "<b>図と木は、段1 が名前付きで持つべき既製品である。</b>"
    "文法だけでも組めるが、意味がどの型でも同じでなければ困る"),
  joint("同じ形の無駄を探すと"),
  step("evidence","測った",
    "<b>種別の鍵が6つある。</b>"
    "どれも「ある欄の値で必須ブロックの集合が変わる」という同じ概念に、"
    "型ごとの名前を付けているだけである"),
  joint("だから"),
  step("conclude","言えること",
    "<b>覆うのではなく、落とす。</b>"
    "実物にある無駄を賄うのは、後方互換を残すのと同じことになる"),
  joint("落とし方も見た"),
  step("evidence","測った",
    "型は4つで99.5%、制限は5つ、<b>分岐は1形しかない</b>。"
    f"{C('pattern')} は正規表現としては一度も使われていない"),
  joint("だから"),
  step("conclude","結論",
    "段1 が部品を提供し、段2 は8つを宣言する。"
    "<b>部品ひとつに行き先が1つ対応するので、型を起こす規則が書ける</b>"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["2つの型が同じ木を別々に組んでいた",'<span class="kindtag unv">実測</span>',
      f"{C('KnowledgeSchema')} の概念の木と {C('SkillSchema')} の手順の親子","—"]),
    ("keyrow",["種別の鍵が6つ",'<span class="kindtag unv">実測</span>',
      "最新版10本の分岐を数えた。枝は計31本","—"]),
    ("",["型4つ・制限5つ・分岐1形",'<span class="kindtag unv">実測</span>',
      "最新版10本の構造の語を数えた",
      "<b>いまの型が表せない構造を、段2 が必要としたとき</b>"]),
    ("",["部品と組み合わせの線引き",'<span class="kindtag lim">利用者の整理</span>',
      "「段1 は表現できる部品を全て提供し、段2 が組み合わせて表現する」","—"]),
  ]))

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>段1 が部品を提供し、段2 が8つを宣言する</h1>'
 '<p class="lede">2つの型が、同じ「深さ有界の木」を別々の名前で自前に組んでいた。'
 '種別の鍵は<b>6つあって、どれも同じ概念</b>である。'
 '<b>覆うのではなく、落とす。</b></p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle は、'
  '<b>段1 が、このスキーマが表現できる部品を全て提供する</b>。'
  '段2 は、その部品だけを使って<b>8つを宣言する</b>。'
  '部品ひとつひとつに、成果物のどこへ落ちるかが1つ対応する ── これが型を起こす規則になる。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt"><b>段2 が自前で部品を組んでいたら、それは段1 の欠落である。</b>'
  '部品だけで組めることが、欠落が無いことの確かめ方になる。'
  'いまは図と木が段2 で自前に組まれている。</span></div></div>'),

 sec("02","段1 が提供する部品",
   "<b>実物にある無駄は賄わない。</b>覆うことは目的ではない。",
   parts1),

 sec("03","段2 が宣言する8つ",
   "すべて段1 の部品で組める。<b>段2 は組み合わせるだけで、部品を作らない。</b>",
   parts2,
   fold("段2 が持たないもの（3件）",
     tbl(["持たないもの","なぜ"],[
       ("",["図と木の形","<b>段1 の標準の組み立て。</b>型ごとに違ってはいけない"]),
       ("",["表紙の宣言","<b>段1。</b>どの型でも同じ"]),
       ("",["索引","<b>保存しない。</b>取り出すときに組み立てる"]),
     ]))),

 sec("04","実物にある無駄で、賄わないもの",
   "<b>無駄を賄えば、後方互換を残すのと同じことになる。</b>"
   "同じ概念に型ごとの名前が付いている箇所を落とす。",
   FIG + waste),

 sec("05","理由",
   "段2 が自前で部品を組んでいる箇所がある。"
   "<b>同じ概念に、型ごとの名前が付いている。</b>",
   reason, reason_fold),

 sec("06","判断を分けた軸",
   "採る案は4つの条件のうち3つを満たす。落とすのは1つで、<b>型10本を書き直す</b>。",
   axis, axis_fold),

 sec("07","付随して決めたこと",
   "部品を確定させると、いくつかの語の行き先が決まる。4点を同時に決めた。",
   tbl(["論点","決定"],[
     ("keyrow",["種別の鍵","<b>1つにする。</b>型ごとの名前をやめる"]),
     ("keyrow",["枝ごとの中身","<b>名前つきの入れ物をやめる。</b>枝は必須ブロックの一覧だけを持つ"]),
     ("",["描き方の語","<b>6語から2語へ。</b>ブロックに付く1つと、型の根に付く1つ"]),
     ("",["入れ子の表し方",
       f"<b>{C('$ref')} の再帰を使わず、深さのぶんだけ展開する。</b>"
       "「再帰は常に有界である」を構造そのもので満たす"]),
   ]),
   fold("それぞれの根拠を開く（4件）",
     tbl(["論点","根拠"],[
       ("keyrow",["種別の鍵",
         "6つとも「ある欄の値で必須ブロックの集合が変わる」という同じ形。"
         "<b>名前が複数あると書き手が選ぶことになり、選ばせている以上それは概念ではない</b>"]),
       ("keyrow",["枝ごとの中身",
         "枝が言うべきなのは「この枝ではこれらのブロックが要る」だけ。"
         "<b>34個の名前つきの入れ物は、その言い方の副産物</b>"]),
       ("",["描き方の語",
         "6語が<b>2つの高さ</b>に分かれると測れた ── ブロックに付く4語と、型の根に付く2語。"
         "高さが違うものはまとめられないが、同じ高さのものはまとまる"]),
       ("",["入れ子の表し方",
         "既にある不変条件が「再帰は常に有界である」と定めている。"
         "<b>展開すれば、守るまでもなく成り立つ</b>"]),
     ]))),

 sec("08","答えないこと",
   "3つ残る。<b>いずれも仕様を書くときか、移すときに決める。</b>",
   tbl(["項目","何が決まっていないか","いつ決めるか"],[
     ("",["各語の名前","「描き方」「成果物の宛先」「種別」は仮","<b>仕様を書くとき</b>"]),
     ("keyrow",["<b>読む必要の度合い</b>","<b>部品として持たない。</b>索引は部品の鍵と説明から導けるので、項目ごとに申告させる必要が無い ── <b>宣言させるものを増やすと、宣言し忘れが黙って落ちる</b>","<b>決着（2026-08-16）</b>"]),
     ("keyrow",["いまの型をどう書き換えるか","対象と順序、その間の互換","<b>移す計画</b>"]),
   ])),

 '<section><h2><span class="num">09</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-16</span></div></section>',

 sec("10","関連","この決定は、Schema のコマンドと Document 側を決めるための土台になる。","",
  fold("縛る対象と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["縛る対象","段1 が提供する部品と、段2 が宣言する8つ"]),
      ("keyrow",["先立つ決定","部品に鍵と説明を持たせ、索引を取り出すときに組み立てる（未承認）── "
        "<b>並びの部品の性質が、そこで決まっている</b>"]),
      ("",["先立つ決定","Schema を仕様から実装し、型は Document として置く（承認済み）"]),
      ("",["先立つ決定","語彙を意味の名前だけにし、構造の部品と共通の欄を主張から分ける（承認済み）"]),
      ("keyrow",["この決定を使う予定",
        "<b>Schema のコマンドを2つに直す</b>（骨格を作る／型を起こす）／"
        "Document 側／移す計画"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>段1 が部品を提供し、段2 が8つを宣言する</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-tier1-tier2.html").write_text(out,encoding="utf-8")
print("書いた",len(out))

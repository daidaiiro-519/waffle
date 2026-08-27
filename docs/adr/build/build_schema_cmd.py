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
a+='<text x="14" y="18" font-size="11" fill="var(--assume)">型を起こす ── 宣言から、型そのものを組み立てる</text>'
a+=gb(14,30,170,44,"段2 の宣言","構造化データ","var(--assume)")
a+=ga(184,52,246,52)
a+=gb(246,30,170,44,"型を起こす","作り手","var(--assume)",True)
a+=ga(416,52,478,52)
a+=gb(478,30,150,44,"段2 の型")
a+='<text x="14" y="106" font-size="11" fill="var(--infer)">骨格を作る ── 型から、実体の器を起こす</text>'
a+=gb(14,118,170,44,"段2 の型＋識別子",None,"var(--infer)")
a+=ga(184,140,246,140)
a+=gb(246,118,170,44,"骨格を作る","型のコマンド","var(--infer)",True)
a+=ga(416,140,478,140)
a+=gb(478,118,150,44,"段3 の骨格","値が空")
FIG=gsvg("0 0 650 180",a,
 "<b>作られる側がまだ存在しないので、どちらも作り手が要る。</b>"
 "違うのは、何を作るか ── 型そのものか、その型の実体の器か。")

cmds = tbl(["操作","何を作るか","入力","誰の"],[
 ("keyrow",["<b>型を起こす</b>","<b>段2 の型そのもの（構造）</b>","段2 の宣言","<b>作り手</b>"]),
 ("keyrow",["<b>骨格を作る</b>","段3 の実体の器（値が空）。器と書き方の指針の両方を返す",
   "段2 の型＋識別子＋種別","<b>段2 のコマンド</b>"]),
 ("",["読み方の指針を返す","そのブロックを何のために読むか","段2 の型＋ブロックの鍵","段2 のコマンド"]),
])

diff = tbl(["","置き換えられた決定","この決定"],[
 ("keyrow",["Schema が持つ操作","<b>1つ</b>（骨格を作る）","<b>3つ</b>（型を起こす／骨格を作る／読み方の指針を返す）"]),
 ("keyrow",["型を起こすこと","<b>視野に入っていなかった</b>","<b>作り手として立てる</b>"]),
 ("",["読み方の指針を返すこと","<b>本文にあるのに、表に無かった</b>","表に載せる"]),
 ("",["Document のコマンド","5つ","<b>変えない</b>（のちに<b>4つ</b>へ ── 終端化するを落とした）"]),
 ("",["参照は持つが解決しない","定めた","<b>引き継ぐ</b>"]),
 ("",["どの段の話か","<b>言っていない</b>","<b>段で言う</b>"]),
])

reason = '<div class="chain">' + "".join([
  step("premise","前提",
    "承認済みの決定で、<b>JSON Schema は宣言から作られるものになった</b>。"
    "段2 の型は Document として宣言され、そこから型が組み立てられる"),
  joint("だから"),
  step("conclude","言えること",
    "<b>宣言から型を組み立てる操作が要る。</b>いまは存在しない ── "
    f"{C('patch-schema')} が「ブロックを足す」「枝を足す」と手続きで積み上げているだけである"),
  joint("これは描くことか、を確かめた"),
  step("premise","前提",
    "<b>描くとは、読み手向けの成果物へ落とすことである。</b>"
    "JSON Schema は人が読むものではなく、機械が使う型なので、同じ操作にはできない"),
  joint("骨格を作ることとも違う"),
  step("conclude","言えること",
    "<b>骨格を作るのは器を用意すること、型を起こすのは器の形そのものを組み立てること。</b>"
    "前者を「骨格」と呼ぶのは自然だが、後者をそう呼ぶのは無理がある"),
  joint("持ち主を見ると"),
  step("premise","前提",
    "<b>作られる側がまだ存在しないので、作り手が要る。</b>"
    "骨格を作るときに使ったのと同じ理屈が、一段上でもう一度出る"),
  joint("表と本文の食い違いも見つかった"),
  step("evidence","測った",
    "置き換えられた決定の本文に「<b>読み方の指針は Schema の別のコマンドが返す</b>」とあるが、"
    "<b>コマンドの表にそのコマンドが無い</b>"),
  joint("合わせると"),
  step("conclude","結論",
    "Schema は<b>3つの操作</b>を持つ ── 型を起こす／骨格を作る／読み方の指針を返す。"
    "Document の5つと、参照の規律は変えない"),
]) + "</div>"

reason_fold = fold("段の裏付けと、崩れるときを開く（4件）",
  tbl(["段","裏付けの種別","参照先","崩れるとき"],[
    ("keyrow",["JSON Schema は宣言から作られる",'<span class="kindtag unv">承認済みの決定</span>',
      "Schema を仕様から実装し、型は Document として置く","—"]),
    ("keyrow",["型を組み立てる操作が無い",'<span class="kindtag unv">実測</span>',
      f"{C('patch-schema')} の操作は "
      f"{C('add_block')}・{C('rename_block')}・{C('add_def')}・{C('add_kind_branch')} ── "
      "すべて手続きで積み上げる形","—"]),
    ("",["表と本文の食い違い",'<span class="kindtag unv">実測</span>',
      "置き換えられた決定の本文3か所と、コマンドの表","—"]),
    ("",["作られる側が存在しないので作り手が要る",'<span class="kindtag lim">確立された型</span>',
      "DDD の作り手（Factory）","作ったあとも作り手が相手を持ち続ける形になったとき"]),
  ]))

body="".join([
 '<header><p class="eyebrow">Architecture Decision Record</p>'
 '<h1>Schema は3つの操作を持つ</h1>'
 '<p class="lede">承認済みの決定で JSON Schema が<b>宣言から作られるもの</b>になった。'
 'ところが<b>宣言から型を組み立てる操作が、どこにも無い</b> ── '
 '手続きでブロックを足していくだけである。</p></header>',

 sec("01","決定",None,
  '<div class="decision"><p class="main">Waffle において、'
  '<b>Schema は3つの操作を持つ</b> ── '
  '<b>型を起こす</b>（段2 の宣言から、型そのものを組み立てる）／'
  '<b>骨格を作る</b>（型から、段3 の実体の器を起こす）／'
  '<b>読み方の指針を返す</b>。'
  'Document の5つと、参照の規律は変えない。</p>'
  '<div class="key"><span class="lbl">決め手</span>'
  '<span class="txt"><b>型を起こすことは、描くことでも骨格を作ることでもない。</b>'
  '描くのは読み手向けの成果物へ落とすことで、JSON Schema は機械が使う型である。'
  '骨格を作るのは器を用意することで、型を起こすのは器の形そのものを組み立てることである。</span></div></div>'),

 sec("02","2つの作り手",
   "<b>作られる側がまだ存在しないので、どちらも作り手が要る。</b>"
   "違うのは、何を作るかである。",
   FIG + cmds),

 sec("03","置き換えた決定との差",
   "<b>あの決定は間違っていない。</b>型を起こすことが視野に入っていなかっただけである。",
   diff,
   fold("なぜ書き直さず、新しく作ったかを開く",
     '<p class="blob">あの決定は<b>一度、上書きで書き直している</b>。'
     'その結果、前の版に何が書いてあったかが文書から辿れなくなり、'
     '<b>食い違いを指摘されるまで気づかなかった</b>。</p>'
     '<p class="blob">今回は訂正ではなく<b>不足の補い</b>である。'
     '間違っていない決定を上書きすると、正しかった判断まで消える。'
     'だから<b>古いほうを「置き換えられた」として残し、新しく作った</b>。</p>'
     '<p class="foldnote"><b>取り下げとは別の状態である</b> ── '
     '取り下げは「誤っていた」、置き換えは「正しかったが範囲が足りなくなった」。</p>')),

 sec("04","理由",
   "宣言から型を組み立てる操作が、どこにも無い。"
   "<b>描くことでも骨格を作ることでもないので、名前を与える。</b>",
   reason, reason_fold),

 sec("05","付随して決めたこと",
   "操作が増えると、名前と段の言い方が決まる。3点を同時に決めた。",
   tbl(["論点","決定"],[
     ("keyrow",["「骨格」という言葉",
       "<b>器を用意することにだけ使う。</b>型を起こすことは骨格と呼ばない"]),
     ("keyrow",["決定は、どの段の話かを言う",
       "<b>「Schema」「Document」だけで書かない。</b>"
       "置き換えられた決定は段を言っておらず、読むたびにどちらの顔の話か分からなくなった"]),
     ("",["読み方の指針を返すこと",
       "<b>操作として表に載せる。</b>本文だけにあって表に無い状態を解く"]),
   ]),
   fold("それぞれの根拠を開く（3件）",
     tbl(["論点","根拠"],[
       ("keyrow",["「骨格」という言葉",
         "骨格とは<b>値を入れる器</b>のことである。"
         "型を起こすのは器の形そのものを組み立てることなので、同じ言葉では指せない"]),
       ("keyrow",["決定は、どの段の話かを言う",
         "段2 は<b>宣言としては Document、型としては Schema</b> という二重の顔を持つ。"
         "段を言わないと、どちらの話か読み手が決められない"]),
       ("",["読み方の指針を返すこと",
         f"この決定は「呼び出せる操作」を操作と呼ぶ（{C('値を取り出す')} も数えている）。"
         "その定義なら、指針を返すことも同じ資格である"]),
     ]))),

 sec("06","答えないこと",
   "2つ残る。<b>どちらも次の決定で扱う。</b>",
   tbl(["項目","何が決まっていないか","いつ決めるか"],[
     ("",["型を起こす規則の中身",
       "部品ひとつひとつの落とし方は定めたが、<b>組み立ての手順</b>は定めていない",
       "<b>仕様を書くとき</b>"]),
     ("keyrow",["Document 側の見直し",
       "コマンド・表紙・状態を、段の言い方で書き直すか",
       "<b>次の決定</b>"]),
   ])),

 '<section><h2><span class="num">07</span>承認</h2>'
 '<div class="approve"><span class="k">状態</span><span class="v">承認済み</span><span class="m">2026-08-16</span></div></section>',

 sec("08","関連","この決定は、コマンドの決定を置き換える。","",
  fold("置き換えの関係と、前後の決定を開く（5件）",
    tbl(["種類","対象"],[
      ("keyrow",["<b>置き換える決定</b>",
        "<b>コマンドを、判断に要るデータのある場所へ戻す</b>（<b>置き換えられた</b>）── "
        "判断はデータのある場所へ置く、参照は持つが解決しない、Document の5つは<b>そのまま引き継ぐ</b>。"
        "Schema の操作だけが1つから3つへ増える"]),
      ("",["先立つ決定","Schema を仕様から実装し、型は Document として置く（承認済み）"]),
      ("",["先立つ決定","段1 が部品を提供し、段2 が8つを宣言する（承認済み）── "
        "<b>型を起こす規則の材料がここにある</b>"]),
      ("",["書き直す文書",
        f"{C('agg-schema')}（廃止して新規）／{C('agg-document')}"]),
      ("",["この決定を使う予定","Document 側の見直し／移す計画"]),
    ]))),
])

extra2 = extra + """
.fig{margin:0;display:flex;flex-direction:column;gap:.6rem}
.fig .scroll{padding:1.1rem 1rem}
figcaption{font-size:.83rem;color:var(--ink-faint);line-height:1.7}
figcaption b{color:var(--ink-soft)}
"""
out=("<title>Schema は3つの操作を持つ</title>"
     f"<style>{CSS}\n{extra2}</style><div class=\"wrap\">{body}</div>")
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/adr-schema-operations.html").write_text(out,encoding="utf-8")
print("書いた",len(out))

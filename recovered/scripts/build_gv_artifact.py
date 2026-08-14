import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from inline_svgs import SVGS

HEAD = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/svg-renderer-capability.html").read_text(encoding="utf-8")
STYLE = HEAD[HEAD.index("<style>"):HEAD.index("</style>") + 8]
STYLE = STYLE.replace("</style>", """
  .gv { display: block; width: 100%; height: auto; max-width: 100%; }
  .plate { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 1.2rem; overflow-x: auto; }
  .plate.tight { padding: .8rem; }
  .verdict { display: inline-flex; align-items: baseline; gap: .35rem; font-family: var(--mono); font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; }
  .verdict.ok  { color: var(--render); }
  .verdict.ng  { color: var(--warn); }
  .case { display: flex; flex-direction: column; gap: .8rem; }
  .case > .head { display: flex; align-items: baseline; gap: .8rem; flex-wrap: wrap; }
  .case h3 { font-size: 1rem; }
  .case .why { font-size: .86rem; color: var(--ink-soft); max-width: 44rem; }
  .grid { display: grid; gap: 2.4rem; }
  @media (min-width: 60rem) { .grid.two { grid-template-columns: 1fr 1fr; } }
</style>""")


def case(cid, title, verdict, why, svg_key, tight=False):
    v = "ok" if verdict == "できた" else "ng"
    mark = "○" if v == "ok" else "✗"
    return f"""
  <div class="case" id="{cid}">
    <div class="head">
      <h3>{title}</h3>
      <span class="verdict {v}">{mark} {verdict}</span>
    </div>
    <p class="why">{why}</p>
    <div class="plate{' tight' if tight else ''}">{SVGS[svg_key]}</div>
  </div>"""


BODY = f"""<title>Graphvizで描ける図・描けない図</title>
{STYLE}

<div class="wrap">

<header>
  <p class="eyebrow">Reference — 実測</p>
  <h1>Graphvizで描ける図・描けない図</h1>
  <p class="lede">図はすべて、この調査のために実際に生成したもの。座標は一行も書いていない。何が美しく出て、何が破綻するかを、能力の軸ごとに当てて確かめた。</p>
  <div class="stats">
    <div class="stat"><b>8</b><span>できた能力</span></div>
    <div class="stat alarm"><b>3</b><span>できなかったこと</span></div>
    <div class="stat alarm"><b>2</b><span>繋ぐときの罠</span></div>
  </div>
</header>

<section id="conclusion">
  <h2><span class="num">00</span>どういう図なら美しく出るか</h2>
  <div class="callout">
    <span class="k">4つの条件</span>
    <p>次の4つを満たす図は、手で座標を書いたものより整った結果になる。ひとつでも外れると、途端に扱いにくくなる。</p>
  </div>
  <div class="scroll">
    <table>
      <caption>表1 ── 美しく出るための条件と、外れたときに起きること</caption>
      <thead><tr><th>条件</th><th>目安</th><th>外れると</th></tr></thead>
      <tbody>
        <tr><td>箱の数が多すぎない</td><td class="n">おおむね 15 以下</td><td>横に延々と伸びる（25個で 3436px）</td></tr>
        <tr><td>関係が階層か、囲みで括れる</td><td class="n">木・DAG・入れ子</td><td>集合が重なる図は作れない</td></tr>
        <tr><td>箱の中身が定型</td><td class="n">見出し＋補足＋状態</td><td>長文は折り返されず一行で伸びる</td></tr>
        <tr><td>縦か横のどちらかに素直に伸びる</td><td class="n">—</td><td>紙に収める操作は縮小しかなく、文字が潰れる</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section id="can">
  <h2><span class="num">01</span>できたこと</h2>
  <div class="grid">
  {case("c-card", "箱の中に表を入れて、カードにする", "できた",
        "HTMLラベルを使うと、見出し帯・本文・補足を別々の大きさと色で積める。角丸の枠に色付きの帯を載せた「カード」が、装飾を手で置かずに出る。<b>見た目の水準を決めているのはこの機能</b>で、これが無いと箱に一行書くだけの図にしかならない。",
        "a-html-card")}
  {case("c-cluster", "囲みを入れ子にし、その境界を跨いで線を引く", "できた",
        "「変更後」の中に「問題空間」「解決空間」を入れ、さらに囲みを跨ぐ破線の矢印を通した。<b>矢印は箱を避けて回り込む。</b>手書きのSVGで最も破綻していた部分が、宣言だけで解ける。",
        "b-nested-cluster")}
  {case("c-port", "箱の中の特定の行から線を出す", "できた",
        "レコード型の箱では、行ごとに識別子を付けて、そこを線の始点にできる。構造体のどのフィールドがどこへ繋がるか、という図が描ける。",
        "c2-port")}
  {case("c-rank", "横一列に揃え、逆流だけ別の線で示す", "できた",
        "同じ段に置く指定と、「並びに影響させない線」の指定が別々にある。工程の並びと、そこへ戻る破線を、干渉させずに描ける。",
        "d-rank-same")}
  {case("c-neato", "階層でない、相互に参照し合う関係", "できた",
        "上下関係の無い網の目は、力学配置に切り替えると解ける。同じ宣言のままエンジンだけを差し替えられる。",
        "e-neato")}
  {case("c-fixed", "座標を自分で決めて、その通りに置かせる", "できた",
        "配置を機械に任せず、こちらで決めることもできる。<b>逃げ道として重要</b>で、どうしても納得のいく配置が出ないときにここへ降りられる。",
        "j-fixed-pos")}
  </div>
</section>

<section id="cannot">
  <h2><span class="num">02</span>できなかったこと</h2>
  <div class="grid">
  {case("x-overlap", "重なる集合を描く", "できなかった",
        "ひとつの箱を2つの囲みに入れようとすると、<b>片方から黙って消える</b>。エラーも警告も出ない。集合の重なりを見せる図は、この道具では作れない。",
        "i-overlap")}
  {case("x-wrap", "長い文を自動で折り返す", "できなかった",
        "左が渡したまま、右が改行を自分で入れた場合。<b>折り返しの判断は一切しない。</b>箱の幅を揃えたければ、文の長さをこちらで管理することになる。",
        "h-wrap")}
  {case("x-scale", "大きくなった図を紙の形へ畳む", "できなかった",
        "25個の箱を横 7 インチに収める指定をした結果。<b>畳むのではなく縮める</b>ので、文字が読めなくなる。折り返して段を作る機能は無い。",
        "k-scale-compressed", tight=True)}
  </div>
</section>

<section id="traps">
  <h2><span class="num">03</span>繋ぐときに引っかかった罠</h2>
  <div class="scroll">
    <table>
      <caption>表2 ── 実際に引っかかったもの</caption>
      <thead><tr><th>何が起きたか</th><th>原因</th><th>対処</th></tr></thead>
      <tbody>
        <tr><td>描いたSVGを画像にできない</td><td>出力の幅と高さが <code>pt</code> 単位で、resvgが受け付けない</td><td>単位を落として <code>viewBox</code> に任せる一行</td></tr>
        <tr><td>行を指す線が、新しい箱として増える</td><td><code>"箱:行"</code> という書き方はPython側の窓口を通らない</td><td><code>tailport</code> で行を指定する</td></tr>
      </tbody>
    </table>
  </div>
  <div class="callout alarm">
    <span class="k">2つ目について</span>
    <p>この罠には<b>実際に引っかかり、一度は「ポートは効かない」と誤って判定した</b>。線は引かれ、絵も出るので、出力を見ただけでは間違いに見えない。名前がそのまま箱になっているところまで見て初めて分かる。</p>
  </div>
</section>

<section id="fit">
  <h2><span class="num">04</span>ADRのfigureに当てはめると</h2>
  <div class="scroll">
    <table>
      <caption>表3 ── ADRで必要になる図と、この道具の適合</caption>
      <thead><tr><th>　</th><th>要る図</th><th>適合</th><th>理由</th></tr></thead>
      <tbody>
        <tr><td><span class="mark yes">○</span></td><td>関門1（構造の対比）</td><td>そのまま乗る</td><td>箱は10個前後、関係は階層、囲みで括れる。4条件を全て満たす</td></tr>
        <tr><td><span class="mark yes">○</span></td><td>関門2（操作と返り値）</td><td>そもそも不要</td><td>縦に並べるだけで、レイアウトの計算が発生しない</td></tr>
        <tr><td><span class="mark no">✗</span></td><td>集合の重なりを見せる図</td><td>乗らない</td><td>この調査の前段で私が作った図が、まさにこれに当たる</td></tr>
      </tbody>
    </table>
  </div>
  <p class="col">3行目は、<a href="https://claude.ai/code/artifact/9dc911bc-48c9-4075-92e5-2b1be9044d3f">前のアーティファクトの図1</a>のこと。入れ子の箱と、外に置いた破線の箱で描いたあの図は、この道具では作れない。<b>ADRの図を全部この道具へ寄せる、とは言えない</b>ということである。</p>
</section>

<footer>
  <p>環境 ── <code>pygraphviz 2.0.1</code>。Graphviz本体を同梱したウィールで、systemへのインストールは無い（<code>dot</code> コマンドも、graphvizのシステムパッケージも存在しない）。取得は <code>uv run --no-project --with pygraphviz</code>。</p>
  <p>掲載した図は全て、この調査のために生成した実物をそのまま埋め込んでいる。作図に使った宣言は最大30行程度で、座標は一行も書いていない。</p>
</footer>

</div>
"""

pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/graphviz-capability.html").write_text(BODY, encoding="utf-8")
print("書いた", len(BODY), "bytes")
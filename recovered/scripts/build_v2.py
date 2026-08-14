import json, pathlib, sys
from html import escape as e
S = pathlib.Path(__file__).parent
sys.path.insert(0, str(S))
from adr_css import ADR_CSS

parts = json.loads((S / "parts_out.json").read_text(encoding="utf-8"))
v2 = json.loads((S / "v2.json").read_text(encoding="utf-8"))
HEAD = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/svg-renderer-capability.html").read_text(encoding="utf-8")
BASE = HEAD[HEAD.index("<style>"):HEAD.index("</style>")]

STYLE = BASE + """
  .part { display:flex; flex-direction:column; gap:.9rem; }
  .part .head { display:flex; align-items:baseline; gap:.7rem; flex-wrap:wrap; }
  .part h3 { font-family:var(--mono); font-size:.95rem; font-weight:600; margin:0; }
  .tag { font-family:var(--mono); font-size:.62rem; letter-spacing:.08em; text-transform:uppercase;
         padding:.1rem .45rem; border-radius:4px; border:1px solid currentColor; }
  .tag.has  { color:var(--render); }
  .tag.none { color:var(--ink-faint); }
  .tag.beta { color:var(--warn); }
  .plate { background:var(--surface); border:1px solid var(--rule); border-radius:10px;
           padding:1rem; overflow-x:auto; }
  .plate pre.mermaid { background:none; border:none; padding:0; margin:0; }
  .grid { display:grid; gap:2.2rem; }
  @media (min-width:66rem) { .grid.two { grid-template-columns:1fr 1fr; } }
  details > summary { cursor:pointer; font-size:.76rem; color:var(--ink-faint); font-family:var(--mono); }
  details pre { margin-top:.6rem; }
""" + ADR_CSS + "</style>"


def mermaid(src):
    return '<div class="plate"><pre class="mermaid">' + e(src) + "</pre></div>"


def syntax(name, what, state, src):
    cls = {"部品あり": "has", "部品なし": "none", "beta・部品なし": "beta"}[state]
    return ('<div class="part"><div class="head"><h3>' + name + '</h3>'
            '<span class="tag ' + cls + '">' + state + "</span></div>"
            '<p class="col">' + what + "</p>" + mermaid(src) + "</div>")


BODY = ["""<title>図の部品と、Markdownで描ける17構文</title>""" + STYLE + """
<div class="wrap">

<header>
  <p class="eyebrow">Reference — 実物</p>
  <h1>図の部品と、Markdownで描ける17構文</h1>
  <p class="lede">図はすべて実際に描かせたもの。部品があるものは部品の出力を、無いものは構文の例をそのまま載せている。どれを部品にするかを決めるための判断材料。</p>
  <div class="stats">
    <div class="stat"><b>17</b><span>Markdownで描ける構文</span></div>
    <div class="stat alarm"><b>4</b><span>うち部品があるもの</span></div>
    <div class="stat"><b>3</b><span>比較の器に入れた中身</span></div>
  </div>
</header>

<section id="naming">
  <h2><span class="num">00</span>名前の見立て</h2>
  <div class="scroll"><table>
    <caption>表1 ── 現状の部品名と、変えるかどうか</caption>
    <thead><tr><th>いまの名前</th><th>由来</th><th>見立て</th></tr></thead>
    <tbody>
      <tr><td><code>sequence</code></td><td>シーケンス図。分野の一般語</td><td>据え置き</td></tr>
      <tr><td><code>flowchart</code></td><td>フローチャート。分野の一般語</td><td>据え置き（向きが選べない）</td></tr>
      <tr><td><code>statediagram</code></td><td>Mermaidの構文名そのもの</td><td><b>states</b> へ</td></tr>
      <tr><td><code>graph</code></td><td>Mermaidの<b>旧</b>構文名</td><td><b>変える</b></td></tr>
      <tr><td><code>architecture</code></td><td>Mermaidの構文名。中身は区画と部品</td><td><b>変える。中身も要検討</b></td></tr>
    </tbody>
  </table></div>
  <div class="callout alarm">
    <span class="k">graph について</span>
    <p>同梱の mermaid-guide が、禁止事項として <b>「<code>graph</code> 構文は使用しない ── <code>flowchart</code> に統一する」</b>と明記しています。部品名がその禁止語のままで、しかも実際の出力は <code>flowchart TB</code> です。<b>名前・出力・自分のガイドの三つが食い違っています。</b></p>
  </div>
</section>

<section id="comparison">
  <h2><span class="num">01</span>比較の図を、器と中身に分ける</h2>
  <p class="col">前に出した比較の図は、<b>中身が木に固定されていました</b>。木でない比較には使えず、今回の話にしか当てはまりません。器の役目は「変更前と変更後を並べて、何が変わったかを見せる」ことだけのはずなので、中身は差し替えられるべきです。</p>
  <div class="scroll"><table>
    <caption>表2 ── 器が持つものと、中身が持つもの</caption>
    <thead><tr><th>　</th><th>持つもの</th><th>知らないもの</th></tr></thead>
    <tbody>
      <tr><td><code>comparison</code>（器）</td><td>面・囲み・面をまたぐ対応・読みの一言</td><td><b>中身が何であるか</b></td></tr>
      <tr><td><code>tree</code>（中身）</td><td>入れ子と、親子をつなぐ線</td><td>それが比較に使われるかどうか</td></tr>
      <tr><td><code>transcript</code>（中身）</td><td>操作と、返ってきたもの</td><td>同上</td></tr>
      <tr><td><code>listing</code>（中身）</td><td>並びと、増えた・減った</td><td>同上</td></tr>
    </tbody>
  </table></div>
  <p class="col">下の3枚は<b>すべて同じ器</b>で、中身だけが違います。器のコードは1つです。</p>
""",
"""  <div class="part"><div class="head"><h3>comparison × tree</h3><span class="tag beta">提案・未実装</span></div>
  <p class="col">入れ子の関係が変わることを見せる。</p>""",
v2["comparisons"]["tree"],
"""  </div>
  <div class="part"><div class="head"><h3>comparison × transcript</h3><span class="tag beta">提案・未実装</span></div>
  <p class="col">同じ操作の返りが変わることを見せる。</p>""",
v2["comparisons"]["transcript"],
"""  </div>
  <div class="part"><div class="head"><h3>comparison × listing</h3><span class="tag beta">提案・未実装</span></div>
  <p class="col">並びから何が落ち、何が増えたかを見せる。<b>増減は色ではなく印（＋ −）で示している。</b></p>""",
v2["comparisons"]["listing"],
"""  </div>
  <div class="callout">
    <span class="k">役割の語彙も直した</span>
    <p>前は <code>focus</code> / <code>moved</code> でした。<code>moved</code> は「置き場所が変わる」という今回の話に固有です。<b><code>unchanged</code> / <code>focus</code> / <code>added</code> / <code>removed</code> / <code>changed</code></b> へ変えました。差分の語彙なので、どの比較でも同じ意味を持ちます。</p>
  </div>
</section>

<section id="existing">
  <h2><span class="num">02</span>いまある部品の実物</h2>
  <div class="grid">
"""]

EXIST = [
    ("sequence", "やり取りの順序。繰り返しと分岐を入れ子で持てる"),
    ("flowchart", "工程の並びと分岐。向きは <code>LR</code> 固定"),
    ("statediagram", "状態と遷移"),
    ("graph", "ものの間の関係。囲みで塊にできる"),
    ("architecture", "区画と、その中の部品。雲と server のアイコンが付く"),
]
for name, what in EXIST:
    BODY.append('<div class="part"><div class="head"><h3>' + name + '</h3>'
                '<span class="tag has">部品あり</span></div>'
                '<p class="col">' + what + "</p>"
                + '<details><summary>渡している構造化データ</summary><pre>'
                + e(json.dumps(parts[name]["input"], ensure_ascii=False, indent=1))
                + "</pre></details>" + mermaid(parts[name]["mermaid"]) + "</div>")

BODY.append("""  </div>
</section>

<section id="all17">
  <h2><span class="num">03</span>部品が無い13構文</h2>
  <p class="col">下は部品を通していません。<b>構文の例として手で書いたもの</b>です。部品にするかどうかを決めるために、何が描けるかだけを見ます。</p>
  <div class="grid">
""")

REST = [
    ("classDiagram", "型と、その関連・多重度", "部品なし"),
    ("erDiagram", "実体と、その関連・多重度", "部品なし"),
    ("quadrantChart", "2軸での位置づけ。<b>subdomainの分類で既に使用中（原文として埋まっている）</b>", "部品なし"),
    ("mindmap", "概念の木。<b>knowledgeのnodesがまさにこの形</b>", "部品なし"),
    ("timeline", "時間順の出来事", "部品なし"),
    ("journey", "体験の段階と、その手応え", "部品なし"),
    ("gantt", "作業と日程", "部品なし"),
    ("pie", "比率", "部品なし"),
    ("gitGraph", "枝分かれと合流", "部品なし"),
    ("requirementDiagram", "要求と、それを満たすもの", "部品なし"),
    ("sankey-beta", "流れの量", "beta・部品なし"),
    ("xychart-beta", "折れ線・棒", "beta・部品なし"),
    ("block-beta", "汎用の箱組み", "beta・部品なし"),
]
for name, what, state in REST:
    BODY.append(syntax(name, what, state, v2["mermaid_extra"][name]))

BODY.append("""  </div>
</section>

<section id="coverage">
  <h2><span class="num">04</span>被覆より先に効くこと</h2>
  <div class="callout alarm">
    <span class="k">原文の逃げ道</span>
    <p>部品が無い図は、<b>原文の塊としてそのまま書けてしまいます</b>。実際 <code>quadrantChart</code> は subdomain の分類図として既に使われていますが、部品を通っていません。書けてしまう限り、構造化されず、検証もされず、HTML側へも展開できません。</p>
    <p><b>「何種類そろえるか」より「原文の逃げ道を閉じるか」の方が先に効きます。</b>閉じると決めれば、実際に使う構文は全部そろえる必要が自動的に出てきます。逆に閉じないままそろえても、書き手は楽な原文へ流れます。</p>
  </div>
  <div class="scroll"><table>
    <caption>表3 ── 進め方の案</caption>
    <thead><tr><th>順</th><th>やること</th><th>そこで分かること</th></tr></thead>
    <tbody>
      <tr><td class="n">1</td><td>実際に原文で書かれている図を数える</td><td>本当に要る構文が、予想でなく実測で決まる</td></tr>
      <tr><td class="n">2</td><td>その分の部品を作る</td><td>—</td></tr>
      <tr><td class="n">3</td><td>原文の逃げ道を閉じる</td><td>ここで初めて不足が違反として現れる</td></tr>
      <tr><td class="n">4</td><td>残りをそろえる</td><td>3で出た不足だけ</td></tr>
    </tbody>
  </table></div>
</section>

<section id="notes">
  <h2><span class="num">05</span>気づいたこと</h2>
  <div class="callout alarm">
    <span class="k">architecture</span>
    <p>実装のコメントに、<b>グループ間の線は3グループ以上で構文解析に失敗する既知の不具合がある</b>と明記され、その回避として常に部品どうしを直接結ぶ形にしてあります。<b>区画どうしの関係を描けません。</b>加えて <code>architecture-beta</code> は beta です。名前より先に、残すかどうかから考える余地があります。</p>
  </div>
  <div class="callout">
    <span class="k">flowchart と graph</span>
    <p>同じ「箱と線」を出すのに、<code>graph</code> は向きを受け取れて <code>flowchart</code> は受け取れません。<b>渡せるものが揃っていません。</b>名前を揃えるなら、受け取るものも一緒に揃えるのが自然です。</p>
  </div>
</section>

<footer>
  <p>出典 ── <code>src/waffle/domain/services/part_renderer.py</code>（417行、15部品）、<code>.claude/skills/mermaid-guide/references/</code>（17構文）。</p>
  <p>「部品あり」の図は部品へ直接データを渡した出力。「部品なし」の図は構文の例として手で書いたもの。比較の3枚は提案した部品の出力。</p>
</footer>

</div>
""")

out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/figure-parts-preview.html")
out.write_text("".join(BODY), encoding="utf-8")
print("書いた", out.stat().st_size, "bytes")
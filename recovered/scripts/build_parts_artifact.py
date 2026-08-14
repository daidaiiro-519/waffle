import json, pathlib
from html import escape as e

S = pathlib.Path(__file__).parent
data = json.loads((S / "parts_out.json").read_text(encoding="utf-8"))
HEAD = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/svg-renderer-capability.html").read_text(encoding="utf-8")
STYLE = HEAD[HEAD.index("<style>"):HEAD.index("</style>") + 8].replace("</style>", """
  .part { display:flex; flex-direction:column; gap:1rem; }
  .part .head { display:flex; align-items:baseline; gap:.8rem; flex-wrap:wrap; }
  .part h3 { font-family:var(--mono); font-size:1rem; font-weight:600; margin:0; }
  .verdict { font-family:var(--mono); font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; }
  .verdict.keep { color:var(--ink-faint); }
  .verdict.rename { color:var(--warn); }
  .cols { display:grid; gap:1.2rem; }
  @media (min-width:64rem) { .cols { grid-template-columns:minmax(0,20rem) minmax(0,1fr); align-items:start; } }
  .plate { background:var(--surface); border:1px solid var(--rule); border-radius:10px; padding:1rem; overflow-x:auto; }
  .plate pre.mermaid { background:none; border:none; padding:0; margin:0; }
  details > summary { cursor:pointer; font-size:.78rem; color:var(--ink-faint); font-family:var(--mono); }
  details pre { margin-top:.6rem; }
</style>""")


def part(key, title, what, verdict, vclass, naming):
    d = data[key]
    return f"""
  <div class="part" id="p-{key}">
    <div class="head"><h3>{key}</h3><span class="verdict {vclass}">{verdict}</span></div>
    <p class="col"><b>{title}</b> ── {what}</p>
    <div class="cols">
      <details><summary>渡している構造化データ</summary><pre>{e(json.dumps(d["input"], ensure_ascii=False, indent=1))}</pre></details>
      <div class="plate"><pre class="mermaid">{e(d["mermaid"])}</pre></div>
    </div>
    <p class="col">{naming}</p>
  </div>"""


BODY = f"""<title>いまの図の部品5つ</title>
{STYLE}
<div class="wrap">

<header>
  <p class="eyebrow">Reference — 実物</p>
  <h1>いまの図の部品5つ</h1>
  <p class="lede">下の図はすべて、部品に実際のデータを渡して出させたものをそのまま載せている。説明用に描いたものではない。名前を見直すかどうかの判断材料として、何が出るかを先に見る。</p>
</header>

<section id="verdicts">
  <h2><span class="num">00</span>名前の見立て</h2>
  <div class="scroll">
    <table>
      <caption>表1 ── 現状の名前と、変えるかどうか</caption>
      <thead><tr><th>いまの名前</th><th>名前の由来</th><th>見立て</th></tr></thead>
      <tbody>
        <tr><td><code>sequence</code></td><td>シーケンス図。分野の一般語</td><td>据え置き</td></tr>
        <tr><td><code>flowchart</code></td><td>フローチャート。分野の一般語</td><td>据え置き</td></tr>
        <tr><td><code>statediagram</code></td><td>Mermaidの構文名そのもの</td><td><b>states</b> へ</td></tr>
        <tr><td><code>graph</code></td><td>Mermaidの旧構文名。何を示すか分からない</td><td><b>変える</b></td></tr>
        <tr><td><code>architecture</code></td><td>Mermaidの構文名。中身は区画と部品</td><td><b>変える。中身も要検討</b></td></tr>
      </tbody>
    </table>
  </div>
  <p class="col"><code>sequence</code> と <code>flowchart</code> は、Mermaidの構文名であると同時に<b>分野の一般語</b>でもあります。HTMLで描くことになっても意味が通るので、据え置きが妥当だと考えます。残り3つは、Mermaid固有の名前か、何を示すか分からない名前です。</p>
</section>

<section id="parts">
  <h2><span class="num">01</span>それぞれ何が出るか</h2>

  {part("sequence", "やり取りの順序", "誰が誰に何を渡し、何が返るか。繰り返しと分岐を入れ子で持てる。", "据え置き", "keep",
        "分野の一般語なので、このままで意味が通ります。")}

  {part("flowchart", "工程の並びと分岐", "段が順に進み、条件付きで戻る。", "据え置き", "keep",
        "同上。ただし出力が <code>flowchart LR</code> 固定で、向きを選べません。")}

  {part("statediagram", "状態と遷移", "何が起きると、どの状態からどの状態へ移るか。", "states へ", "rename",
        "<code>stateDiagram-v2</code> というMermaidの構文名がそのまま部品名になっています。示しているのは<b>状態と遷移</b>なので、<code>states</code> が素直です。")}

  {part("graph", "ものの間の関係", "箱と、箱をつなぐ線。囲みで塊にできる。", "変える", "rename",
        "<b>いちばん問題のある名前</b>です。<code>graph</code> はMermaidの旧い構文名で、実際の出力は <code>flowchart TB</code>。名前と出力が既にずれており、しかも「何を示す部品か」が名前から分かりません。示しているのは<b>ものの間の関係</b>です。")}

  {part("architecture", "区画と、その中の部品", "区画を作り、中に部品を置き、部品どうしを結ぶ。", "変える", "rename",
        "Mermaidの <code>architecture-beta</code> をそのまま使っています。<b>雲と server のアイコンが付く</b>ので、見た目がインフラ図に寄ります。層と依存を示す用途で使うと、アイコンの意味が内容と合いません。名前は <code>zones</code> が実態に近いですが、<b>中身の方も見直す価値があります</b>。")}
</section>

<section id="caveat">
  <h2><span class="num">02</span>気づいたこと</h2>
  <div class="callout alarm">
    <span class="k">architecture について</span>
    <p>部品の実装に、<b>グループ間の線は3グループ以上で構文解析に失敗する既知の不具合がある</b>とコメントで明記されており、その回避として常に部品どうしを直接結ぶ形にしてあります。つまり<b>区画どうしの関係を描けません</b>。区画を跨ぐ依存を示したいときに、線が部品レベルまで降りてしまいます。</p>
    <p>加えて <code>architecture-beta</code> は名前のとおり beta です。名前を変えるかどうかとは別に、<b>この部品を残すかどうか</b>から考える余地があります。</p>
  </div>
  <div class="callout">
    <span class="k">flowchart について</span>
    <p>向きが <code>LR</code> に固定されています。<code>graph</code> は <code>direction</code> を受け取れるのに、<code>flowchart</code> は受け取れません。同じ「箱と線」を出す部品どうしで、渡せるものが揃っていません。</p>
  </div>
</section>

<footer>
  <p>出典 ── <code>src/waffle/domain/services/part_renderer.py</code>（417行、15部品）。図はすべて、そこの関数へ直接データを渡して得た出力そのもの。</p>
</footer>

</div>
"""
pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/figure-parts-preview.html").write_text(BODY, encoding="utf-8")
print("書いた", len(BODY), "bytes")
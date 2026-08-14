"""17種のアーティファクトを組み立てる。図の中身は build_artifact17.py が先に出す。"""
import pathlib

HERE = pathlib.Path(__file__).parent

PAGE = """
  *{box-sizing:border-box}
  body{margin:0;padding:clamp(1.5rem,4vw,3rem) clamp(1rem,3vw,2rem) 5rem;
       background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.8}
  main{max-width:74rem;margin:0 auto;display:flex;flex-direction:column;gap:1.6rem}
  header.top{display:flex;flex-direction:column;gap:.8rem;margin-bottom:.6rem}
  .eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.16em;
           text-transform:uppercase;color:var(--ink-faint)}
  h1{font-size:clamp(1.6rem,4vw,2.2rem);line-height:1.35;font-weight:600;margin:0}
  .lede{color:var(--ink-soft);font-size:1rem;margin:0;max-width:40rem}
  .stats{display:flex;flex-wrap:wrap;gap:2rem;padding-top:1rem;border-top:1px solid var(--rule)}
  .stat{display:flex;flex-direction:column}
  .stat b{font-family:var(--mono);font-size:1.4rem;font-weight:600;line-height:1.2}
  .stat span{font-size:.76rem;color:var(--ink-faint)}
  .note{border-left:3px solid var(--acc);background:var(--surface);padding:1rem 1.2rem;
        border-radius:0 10px 10px 0;display:flex;flex-direction:column;gap:.5rem}
  .note.warn{border-left-color:var(--warn);background:var(--warn-bg)}
  .note .k{font-family:var(--mono);font-size:.64rem;letter-spacing:.12em;
           text-transform:uppercase;color:var(--ink-faint)}
  .note p{margin:0;max-width:46rem;font-size:.88rem}
  .card{background:var(--surface);border:1px solid var(--rule);border-radius:12px;
        padding:1rem 1.1rem 1.3rem;display:flex;flex-direction:column;gap:.8rem}
  .card header{display:flex;align-items:baseline;gap:.7rem;flex-wrap:wrap}
  .card h2{font-family:var(--mono);font-size:.9rem;margin:0}
  .fam{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;padding:.08rem .4rem;
       border-radius:4px;border:1px solid currentColor}
  .fam--graph{color:var(--acc)} .fam--chart{color:var(--warn)}
  .what{font-size:.78rem;color:var(--ink-soft)}
  .pair{display:grid;gap:1rem}
  @media (min-width:62rem){.pair{grid-template-columns:1fr 1fr}}
  .half{display:flex;flex-direction:column;gap:.35rem;min-width:0}
  .tag{font-family:var(--mono);font-size:.6rem;letter-spacing:.06em;color:var(--ink-faint)}
  .tag.mine{color:var(--acc)}
  .stage{background:var(--paper);border-radius:8px;padding:1rem .8rem;overflow-x:auto;
         min-height:5rem;display:flex;align-items:center;justify-content:center}
  .stage pre.mermaid{background:none;border:none;padding:0;margin:0}
  .fail{color:var(--warn);font-size:.85rem}
  table{border-collapse:collapse;width:100%;font-size:.86rem}
  th,td{text-align:left;vertical-align:top;padding:.55rem .7rem;
        border-bottom:1px solid var(--rule-soft);line-height:1.65}
  thead th{font-size:.7rem;color:var(--ink-faint);border-bottom:1px solid var(--rule)}
  tbody tr:last-child td{border-bottom:none}
  code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
       padding:.1em .38em;border-radius:4px}
  footer{border-top:1px solid var(--rule);padding-top:1.2rem;font-size:.8rem;
         color:var(--ink-faint);display:flex;flex-direction:column;gap:.4rem}
"""

TOP = """<header class="top">
  <p class="eyebrow">実現可能性の検証 — 完成イメージ</p>
  <h1>Mermaidの17種を、Waffleで描く</h1>
  <p class="lede">左がMermaid、右がWaffleの描画。どちらもこのページで実際に描かれたもので、画像の貼り付けではない。右はすべて自前のSVGで、見た目はこちらのCSSが決めている。</p>
  <div class="stats">
    <div class="stat"><b>17 / 17</b><span>描けた種類</span></div>
    <div class="stat"><b>0</b><span>追加インストール</span></div>
    <div class="stat"><b>0</b><span>閲覧時のJS（Waffle側）</span></div>
  </div>
</header>

<div class="note">
  <span class="k">この検証が答えていること</span>
  <p><b>Mermaidと同じ見た目を作ることが目的ではない。</b>Mermaidが表せることは下限であって上限ではなく、SVGにCSSを当てられる以上そこは当然に届く、というのがこの検証の前提だった。確かめたのは<b>その前提が本当に成り立つか</b>である。</p>
</div>

<div class="note">
  <span class="k">2つの描き方</span>
  <p><b>点と線</b>（7種）は Graphviz に座標と経路を解かせ、<b>数値だけ</b>を受け取ってSVGを自前で組む。Graphvizの語彙（クラス名・DOT・SVG）は1つも越えてこない。<b>図表</b>（10種）はGraphvizを通さない。値から位置が一意に決まるので、算術だけで描ける。</p>
</div>
"""

TAIL = """
<section class="card">
  <header><h2>この検証で分かった性質</h2><span class="what">正直に</span></header>
  <div class="note warn">
    <span class="k">難しかったのは何か</span>
    <p>難しかったのは<b>アルゴリズムではなく細部の数</b>だった。方式が成立するかは早い段階で分かったが、そこから読める図にするまでに崩れを十数件直している。しかも<b>同じ種類の失敗が繰り返し出た</b>——CSSの重なり順、寸法の見積もり、単に描き忘れ。</p>
    <p><b>方式の限界には一度も当たっていない。</b>残っているのは作り込みの量であり、上限はMermaidではない。</p>
  </div>
  <table>
    <thead><tr><th>直したもの</th><th>原因の種類</th></tr></thead>
    <tbody>
      <tr><td>箱から文字がはみ出す</td><td>寸法を見積もりで決めていた。書体の字幅表から実測するようにした</td></tr>
      <tr><td>区画の文字が中央に寄る</td><td>CSSの重なり順（<code>.wf-node text</code> が <code>.wf-row</code> に勝っていた）</td></tr>
      <tr><td>辺の両端の記号が出ない</td><td>マーカー任せをやめ、経路の向きから自分で描くようにした</td></tr>
      <tr><td>ラベル同士が近い</td><td>間隔の設定を渡していなかった</td></tr>
      <tr><td>実行中の帯が無い</td><td>単に未実装だった</td></tr>
      <tr><td>開始・終了が空の箱になる</td><td>役割ごとの形を持っていなかった</td></tr>
    </tbody>
  </table>
</section>

<footer>
  <p>点と線 ── <code>pygraphviz</code>（macOS / Linux / Windows すべてにバイナリ同梱ウィールが配布されており、システムへのインストールは不要）に座標を解かせ、矩形・経路・囲みの数値だけを受け取ってSVGを組み立てている。</p>
  <p>図表 ── 外部の道具を使わない。軸・帯・割合・格子は値から位置が決まるため、その場の算術で描いている。</p>
  <p>Markdown成果物は従来どおりMermaidのまま。この方式はHTMLで出すときにだけ使う。</p>
</footer>
"""


def main():
    body = (HERE / "artifact17_body.html").read_text(encoding="utf-8")
    figcss = (HERE / "artifact17_css.txt").read_text(encoding="utf-8")
    html = ("<title>Mermaidの17種を、Waffleで描く</title>"
            f"<style>{figcss}{PAGE}</style>"
            f"<main>{TOP}{body}{TAIL}</main>")
    out = pathlib.Path("/home/daidaiiro/workspace/waffle/docs/adr/waffle-17-figures.html")
    out.write_text(html, encoding="utf-8")
    print("書いた", out.stat().st_size, "bytes / 自前SVG",
          body.count("<svg"), "枚 / mermaid", body.count('class="mermaid"'), "枚")


if __name__ == "__main__":
    main()

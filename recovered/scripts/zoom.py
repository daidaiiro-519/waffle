"""1枚だけ大きく描いて、端の見え方を確かめる。"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build import FIGS
from svg_graph import render_graph, CSS as GCSS
from svg_chart import render_chart, CSS as CCSS
from styles import CSS
from tokens import LOOK

want = sys.argv[1:]
out = []
for name, what, _o, data in FIGS:
    if name not in want:
        continue
    svg = render_graph(data) if data["kind"] in ("graph",) else render_chart(data)
    out.append(f'<section><h2>{name}</h2><div class="z">{svg}</div></section>')
html = ('<title>拡大</title><style>' + CSS + LOOK + GCSS + CCSS + """
  body{margin:0;padding:24px;background:var(--paper);font-family:var(--sans)}
  h2{font-family:var(--mono);font-size:.8rem;color:var(--ink-faint);margin:0 0 .5rem}
  section{margin-bottom:28px}
  .z{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:20px;
     display:inline-block;zoom:2.2}
""" + '</style><main>' + "".join(out) + '</main>')
pathlib.Path("../shot/zoom.html").write_text(html, encoding="utf-8")
print("拡大ページ", len(out), "枚")
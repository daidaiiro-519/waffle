"""同じ内容を、Mermaidと自前で並べる。差を1件ずつ数えるための台。"""
import json
import pathlib
import sys
from html import escape as e

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build import FIGS              # noqa: E402
from figures import render          # noqa: E402
from styles import CSS              # noqa: E402

S = pathlib.Path(__file__).parent.parent
MMD = json.loads((S / "all_mermaid_themed.json").read_text(encoding="utf-8"))

PAIR = {
    "flowchart": "flowchart", "state": "statediagram", "class": "classDiagram",
    "er": "erDiagram", "architecture": "architecture", "requirement": "requirementDiagram",
    "mindmap": "mindmap", "sequence": "sequence", "gantt": "gantt", "timeline": "timeline",
    "journey": "journey", "pie": "pie", "xychart": "xychart-beta", "sankey": "sankey-beta",
    "quadrant": "quadrantChart", "gitGraph": "gitGraph", "block": "block-beta",
}

PAGE = """
  *{box-sizing:border-box}
  body{margin:0;padding:1.2rem;background:var(--paper);color:var(--ink);font-family:var(--sans)}
  main{display:flex;flex-direction:column;gap:1.2rem}
  .row{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:.9rem 1rem 1.1rem}
  .row h2{font-family:var(--mono);font-size:.85rem;margin:0 0 .7rem;display:flex;gap:.7rem;align-items:baseline}
  .row h2 span{font-family:var(--sans);font-size:.72rem;color:var(--ink-faint);font-weight:400}
  .pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start}
  .half{display:flex;flex-direction:column;gap:.4rem;min-width:0}
  .tag{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;color:var(--ink-faint)}
  .tag.mine{color:var(--acc)}
  .stage{background:var(--paper);border-radius:8px;padding:1rem .8rem;display:flex;
         justify-content:center;overflow-x:auto;min-height:6rem;align-items:center}
  .stage pre.mermaid{background:none;border:none;padding:0;margin:0}
"""

SCRIPT = (
    '<script type="module">'
    "import mermaid from './node_modules/mermaid/dist/mermaid.esm.min.mjs';"
    "mermaid.initialize({startOnLoad:false, securityLevel:'loose'});"
    "await mermaid.run({querySelector:'pre.mermaid'});"
    "window.__done = true;"
    "</script>"
)


def main():
    rows = []
    for name, what, _origin, data in FIGS:
        key = PAIR.get(name)
        if not key or key not in MMD:
            continue
        rows.append(
            '<section class="row"><h2>' + name + "<span>" + what + "</span></h2>"
            '<div class="pair">'
            '<div class="half"><span class="tag">Mermaid</span>'
            '<div class="stage"><pre class="mermaid">' + e(MMD[key]) + "</pre></div></div>"
            '<div class="half"><span class="tag mine">自前 HTML+CSS</span>'
            '<div class="stage">' + render(data) + "</div></div>"
            "</div></section>")

    html = ('<!doctype html><meta charset="utf-8"><title>並べて数える</title>'
            "<style>" + CSS + PAGE + "</style>"
            "<main>" + "".join(rows) + "</main>" + SCRIPT)
    out = S / "shot" / "compare.html"
    out.write_text(html, encoding="utf-8")
    print("並べた", len(rows), "組 /", out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

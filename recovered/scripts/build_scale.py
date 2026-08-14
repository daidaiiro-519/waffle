import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scale_data import mine, mermaid, NODES, EDGES   # noqa: E402
from figures import render                            # noqa: E402
from styles import CSS                                # noqa: E402
from html import escape as e                          # noqa: E402

PAGE = """
 *{box-sizing:border-box}
 body{margin:0;padding:1rem;background:var(--paper);color:var(--ink);font-family:var(--sans)}
 h2{font-family:var(--mono);font-size:.8rem;margin:0 0 .5rem}
 .row{background:var(--surface);border:1px solid var(--rule);border-radius:10px;
      padding:.8rem;margin-bottom:1rem}
 .stage{background:var(--paper);border-radius:8px;padding:1rem;overflow:auto}
 .stage pre.mermaid{background:none;border:none;padding:0;margin:0}
"""
html = ('<!doctype html><meta charset="utf-8"><title>規模で比べる</title>'
        f'<style>{CSS}{PAGE}</style>'
        f'<main><section class="row" id="mmd"><h2>Mermaid ({len(NODES)}点 {len(EDGES)}線)</h2>'
        f'<div class="stage"><pre class="mermaid">{e(mermaid())}</pre></div></section>'
        f'<section class="row" id="mine"><h2>自前 HTML+CSS ({len(NODES)}点 {len(EDGES)}線)</h2>'
        f'<div class="stage">{render(mine())}</div></section></main>'
        '<script type="module" src="./compare.js"></script>')
out = pathlib.Path(__file__).parent.parent / "shot" / "scale.html"
out.write_text(html, encoding="utf-8")
print("書いた", out.stat().st_size, "bytes")
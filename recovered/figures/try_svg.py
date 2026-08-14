import json, pathlib, sys
sys.path.insert(0, ".")
from svg_graph import render_svg, CSS as GCSS
from styles import CSS
from html import escape as e

d = json.loads(pathlib.Path("real14b.json").read_text(encoding="utf-8"))
PAGE = ("*{box-sizing:border-box}body{margin:0;padding:1rem;background:var(--paper);"
        "color:var(--ink);font-family:var(--sans)}"
        "h2{font-family:var(--mono);font-size:.8rem;margin:0 0 .5rem}"
        ".row{background:var(--surface);border:1px solid var(--rule);border-radius:10px;"
        "padding:.8rem;margin-bottom:1rem}"
        ".stage{background:var(--paper);border-radius:8px;padding:1.4rem;overflow:auto}"
        ".stage pre.mermaid{background:none;border:none;padding:0;margin:0}")
html = ('<!doctype html><meta charset="utf-8"><title>Graphviz座標＋自前SVG</title>'
        f'<style>{CSS}{GCSS}{PAGE}</style><main>'
        f'<section class="row" id="mmd"><h2>Mermaid</h2>'
        f'<div class="stage"><pre class="mermaid">{e(d["mermaid"])}</pre></div></section>'
        f'<section class="row" id="mine"><h2>Graphvizの座標 ＋ 自前SVG ＋ こちらのCSS</h2>'
        f'<div class="stage">{render_svg(d["mine"])}</div></section></main>'
        '<script type="module" src="./compare.js"></script>')
pathlib.Path("../shot/svgtry.html").write_text(html, encoding="utf-8")
print("組んだ")
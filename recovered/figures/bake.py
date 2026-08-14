"""Mermaidの元をSVGへ焼く。Pythonとブラウザだけで、Nodeは使わない。"""
import pathlib
import sys
from playwright.sync_api import sync_playwright

MERMAID_JS = pathlib.Path(sys.argv[1])          # 同梱しておく mermaid.min.js
SRC = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")

PAGE = (
    '<!doctype html><meta charset="utf-8">'
    f"<script>{MERMAID_JS.read_text(encoding='utf-8')}</script>"
    "<body><div id=\"o\"></div></body>"
)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium-headless-shell")
    page = browser.new_page()
    page.set_content(PAGE, wait_until="load")
    svg = page.evaluate(
        """async (src) => {
             mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
             const { svg } = await mermaid.render('baked', src);
             return svg;
           }""",
        SRC,
    )
    browser.close()

out = pathlib.Path(sys.argv[3])
out.write_text(svg, encoding="utf-8")
print(f"焼いた: {out.name}  {len(svg.encode()):,} bytes  （元のmermaid.min.js は {MERMAID_JS.stat().st_size:,} bytes）")
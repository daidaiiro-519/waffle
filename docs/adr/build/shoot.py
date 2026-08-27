#!/usr/bin/env python3
"""完成イメージのHTMLを、Artifactと同じ包みに入れて描画し、PNGへ落とす。

使い方:
    export LD_LIBRARY_PATH=~/.cache/waffle-shoot-libs
    uv run --no-project --with playwright python3 docs/adr/build/shoot.py <html> [出力先]

デスクトップ幅・スマホ幅・暗い紙面の3枚を、ページ全体を収めて撮る。
横方向のはみ出しは画素数で報告する（0でなければ、その幅で紙面が壊れている）。

前提: playwright の chromium を入れておく（`python -m playwright install chromium`）。
この環境には libasound.so.2 が無く、そのままでは起動しない。
libasound2t64 の .deb から取り出したものを ~/.cache/waffle-shoot-libs に置いてあるので、
上記のとおり LD_LIBRARY_PATH を通してから実行する。
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

SHELL = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<style>:root{color-scheme:light}body{margin:0;padding:0;'
         'font:14px system-ui,sans-serif;background:#faf9f5;color:#141413}'
         'img{max-width:100%}</style></head><body>{body}</body></html>')

WIDTHS = [("desktop", 1100, "light"), ("mobile", 390, "light"), ("dark", 1100, "dark")]


def shoot(src: pathlib.Path, out_dir: pathlib.Path) -> list[pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    page_html = SHELL.replace("{body}", src.read_text(encoding="utf-8"))
    tmp = out_dir / (src.stem + ".wrapped.html")
    tmp.write_text(page_html, encoding="utf-8")
    shots = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, width, scheme in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 900},
                                    device_scale_factor=2 if width < 500 else 1,
                                    color_scheme=scheme)
            page.goto(tmp.as_uri())
            page.wait_for_timeout(300)
            # 横はみ出しは、ここで数値として拾える
            overflow = page.evaluate(
                "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            shot = out_dir / f"{src.stem}-{name}.png"
            page.screenshot(path=str(shot), full_page=True)
            print(f"{shot}  (横はみ出し {overflow}px)")
            if overflow > 0:
                print(f"  x {name}: 横スクロールが出ている")
            shots.append(shot)
            page.close()
        browser.close()
    return shots


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/shots")
    shoot(src, out)

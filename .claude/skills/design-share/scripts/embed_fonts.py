#!/usr/bin/env python3
"""embed_fonts.py — 自己完結アセット層: バンドル済みwoff2を data URI としてHTMLへ埋め込む

design-share が「商用級モックを外部依存ゼロで出す」ための道具。
生成したモックHTMLの @font-face に `url(FONT:<name>)` というマーカーを書いておき、
このスクリプトが assets/fonts/<name>.woff2 を base64 の data URI に置換する。
（フォントはあらかじめ Latin subset の woff2 として同梱済み。ランタイム依存は python3 標準のみ。
  CJK等でサブセットが要る場合のみ、別途 fonttools+brotli で font を用意する = prepare_font 参照）

使い方:
    python3 embed_fonts.py <html-file> [--fonts-dir <dir>] [--out <file>]
      既定の fonts-dir は このスクリプトから見た ../assets/fonts
      --out 省略時は入力HTMLを上書き（生成物なので破壊的でよい）

マーカー例（生成HTML側）:
    @font-face{font-family:UI;font-weight:400;src:url(FONT:lato-400) format('woff2')}
"""
import sys, os, re, base64, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--fonts-dir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = a.fonts_dir or os.path.join(here, "..", "assets", "fonts")
    fonts_dir = os.path.abspath(fonts_dir)

    html = open(a.html, encoding="utf-8").read()
    used = set(re.findall(r"url\(FONT:([A-Za-z0-9_-]+)\)", html))
    if not used:
        print("embed_fonts: FONT: マーカーが見つかりません（既に埋め込み済みか、マーカー未使用）", file=sys.stderr)
    cache = {}
    for name in used:
        path = os.path.join(fonts_dir, name + ".woff2")
        if not os.path.isfile(path):
            print(f"embed_fonts: フォントが見つかりません: {path}", file=sys.stderr)
            sys.exit(1)
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        cache[name] = b64
    total = 0
    def repl(m):
        nonlocal total
        b64 = cache[m.group(1)]; total += len(b64)
        return "url(data:font/woff2;base64," + b64 + ")"
    out = re.sub(r"url\(FONT:([A-Za-z0-9_-]+)\)", repl, html)

    dest = a.out or a.html
    open(dest, "w", encoding="utf-8").write(out)
    print(f"embed_fonts: {len(used)} 書体を埋め込み（base64 {total//1024} KB相当） -> {dest}")

if __name__ == "__main__":
    main()

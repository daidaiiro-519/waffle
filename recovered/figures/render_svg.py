"""HTML に埋めた手書きSVGを、実際に描いて画像にする。

描いた結果を目で確かめるための道具。CSS変数とクラス指定は
svglib が解さないので、描く前に実際の値へ展開する。
"""
from __future__ import annotations

import pathlib
import re
import sys

from reportlab.graphics import renderPM
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg

JP = pathlib.Path.home() / ".local/share/fonts/NotoSansJP.ttf"
for name in ("NotoSansJP", "Helvetica", "Helvetica-Bold", "Courier", "Courier-Bold"):
    try:
        pdfmetrics.registerFont(TTFont(name, str(JP)))
    except Exception:
        pass

# 図の中で使っているクラスごとの文字指定
CLASS_FONT = {
    "t":  ('NotoSansJP', "12.5"),
    "s":  ('NotoSansJP', "10.5"),
    "mo": ('NotoSansJP', "10.5"),
}


def expand(html: str, svg: str) -> str:
    """CSS変数とクラス指定を、実際の値へ展開する。"""
    root = re.search(r":root\s*\{([^}]*)\}", html)
    vars_ = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1))) if root else {}

    def sub(m):
        name, fallback = m.group(1), m.group(2)
        return vars_.get(name, (fallback or "#888888").strip()).strip()

    svg = re.sub(r"var\((--[\w-]+)(?:,\s*([^)]+))?\)", sub, svg)

    def inline(m):
        tag, cls = m.group(0), m.group(1)
        for c in cls.split():
            if c in CLASS_FONT:
                fam, size = CLASS_FONT[c]
                return tag[:-1] + f' font-family="{fam}" font-size="{size}"' + tag[-1]
        return tag

    return re.sub(r"<text[^>]*class=\"([^\"]+)\"[^>]*>", inline, svg)


def render(html_path: str, out_dir: str) -> list[str]:
    html = pathlib.Path(html_path).read_text(encoding="utf-8")
    stem = pathlib.Path(html_path).stem
    made = []
    for i, m in enumerate(re.finditer(r"<svg[\s\S]*?</svg>", html)):
        svg = expand(html, m.group(0))
        tmp = pathlib.Path(out_dir) / f"{stem}-{i}.svg"
        tmp.write_text(svg, encoding="utf-8")
        drawing = svg2rlg(str(tmp))
        png = pathlib.Path(out_dir) / f"{stem}-{i}.png"
        renderPM.drawToFile(drawing, str(png), fmt="PNG", dpi=144, bg=0xEDF0F3)
        made.append(str(png))
        print(f"  描いた: {png.name}  {drawing.width:.0f}x{drawing.height:.0f}")
    return made


for p in sys.argv[1:-1]:
    print(f"── {pathlib.Path(p).name}")
    render(p, sys.argv[-1])
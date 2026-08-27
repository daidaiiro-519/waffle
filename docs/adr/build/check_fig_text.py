"""図の文字が箱からはみ出していないかを見る。

描画の検査（render_svg_check）は線と文字の衝突を見ない。PNG を目で見ても、
枠と文字が同じ色調だと気づけない。文字幅は計算できるので、ここで測る。

幅の見積り ── 全角はほぼ字送りぶん、半角はその半分強。
書体によって前後するので、余白を取って「明らかに超えている」ものだけを挙げる。
"""
from __future__ import annotations

import re
import sys
import pathlib

PAD = 16          # 箱の内側に残しておきたい余白（左右合計）。
                  # 22 まで上げても、いまの図は1件も引っかからない
TOLERANCE = 1.02  # 見積りの誤差ぶん。これを超えたら挙げる


def char_width(ch: str, size: float) -> float:
    o = ord(ch)
    if o < 0x2E80:                      # ASCII と記号
        return size * (0.30 if ch == " " else 0.55)
    if 0xFF61 <= o <= 0xFF9F:           # 半角カナ
        return size * 0.5
    return size * 0.98                  # 全角


def text_width(s: str, size: float) -> float:
    return sum(char_width(c, size) for c in s)


def check(path: pathlib.Path) -> int:
    src = path.read_text(encoding="utf-8")
    bad = 0
    for fi, svg in enumerate(re.findall(r"<svg.*?</svg>", src, re.S), 1):
        rects = [(float(m["x"]), float(m["y"]), float(m["w"]), float(m["h"]))
                 for m in re.finditer(
                     r'<rect x="(?P<x>[-\d.]+)" y="(?P<y>[-\d.]+)" '
                     r'width="(?P<w>[-\d.]+)" height="(?P<h>[-\d.]+)"', svg)]
        for m in re.finditer(
                r'<text x="(?P<x>[-\d.]+)" y="(?P<y>[-\d.]+)"[^>]*?'
                r'font-size="(?P<fs>[\d.]+)"[^>]*>(?P<t>[^<]*)</text>', svg):
            t = m["t"].strip()
            if not t:
                continue
            x, y, fs = float(m["x"]), float(m["y"]), float(m["fs"])
            w = text_width(t, fs)
            # その文字を囲んでいる箱（中心が入っているもの）のうち、最も小さいもの
            inside = [r for r in rects if r[0] <= x <= r[0] + r[2] and r[1] <= y <= r[1] + r[3]]
            if not inside:
                continue
            rx, ry, rw, rh = min(inside, key=lambda r: r[2])
            if w > (rw - PAD) * TOLERANCE:
                print(f"   × {path.name} 図{fi}: 「{t}」")
                print(f"       文字 約{w:.0f} / 箱 {rw:.0f}（余白{PAD}）── "
                      f"約{w - rw + PAD:.0f} はみ出し")
                bad += 1
    return bad


def main(argv: list[str]) -> int:
    paths = [pathlib.Path(a) for a in argv[1:]]
    if not paths:
        paths = sorted(pathlib.Path("docs/adr").glob("*.html"))
    total = sum(check(p) for p in paths)
    print(f"はみ出し: {total} 件")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

"""手書きSVGの幾何を静的に確かめる。

レンダリング結果を見られないので、座標と推定幅から
はみ出し・重なり・見切れを機械で見つける。
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
# クラスごとの字送り（全角=1.0em, 半角=0.55em の概算）
FONT = {"t": 12.5, "s": 10.5, "mo": 10.5}


def width_of(text: str, size: float) -> float:
    w = 0.0
    for ch in text:
        w += size * (1.0 if ord(ch) > 0x2E80 else 0.55)
    return w


def check(path: str) -> list[str]:
    src = open(path, encoding="utf-8").read()
    out: list[str] = []
    for m in re.finditer(r"<svg[^>]*viewBox=\"([^\"]+)\"[\s\S]*?</svg>", src):
        vb = [float(v) for v in m.group(1).split()]
        root = ET.fromstring(m.group(0))
        rects = [(float(r.get("x", 0)), float(r.get("y", 0)),
                  float(r.get("width", 0)), float(r.get("height", 0)))
                 for r in root.iter(f"{NS}rect")]

        for r in root.iter(f"{NS}rect"):
            x, y = float(r.get("x", 0)), float(r.get("y", 0))
            w, h = float(r.get("width", 0)), float(r.get("height", 0))
            if x < vb[0] or y < vb[1] or x + w > vb[0] + vb[2] or y + h > vb[1] + vb[3]:
                out.append(f"枠がviewBoxからはみ出し: x={x} y={y} w={w} h={h}")

        for t in root.iter(f"{NS}text"):
            cls = (t.get("class") or "").split()
            size = next((FONT[c] for c in cls if c in FONT), 11.0)
            txt = "".join(t.itertext())
            tw = width_of(txt, size)
            x, y = float(t.get("x", 0)), float(t.get("y", 0))
            anchor = t.get("text-anchor", "start")
            left = x - tw / 2 if anchor == "middle" else x
            right = left + tw
            if left < vb[0] or right > vb[0] + vb[2]:
                out.append(f"文字がviewBoxから見切れ: 「{txt}」 x={left:.0f}..{right:.0f} / 幅{vb[2]}")
            # 収まるべき枠を探す（中心が入っている枠）
            cx, cy = (left + right) / 2, y - size * 0.35
            host = [(rx, ry, rw, rh) for rx, ry, rw, rh in rects
                    if rx <= cx <= rx + rw and ry <= cy <= ry + rh]
            if host:
                rx, ry, rw, rh = min(host, key=lambda r: r[2] * r[3])
                if left < rx + 2 or right > rx + rw - 2:
                    out.append(f"文字が枠からはみ出し: 「{txt}」 文字幅{tw:.0f} > 枠幅{rw}")
    return out


ok = True
for p in sys.argv[1:]:
    issues = check(p)
    print(f"── {p.rsplit('/',1)[-1]}")
    if issues:
        ok = False
        for i in issues:
            print(f"   ✗ {i}")
    else:
        print("   ✓ はみ出し・見切れなし")
sys.exit(0 if ok else 1)
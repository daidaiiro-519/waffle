"""囲みと、その中に置いたものの関係を検査する。

viewBox からのはみ出しだけを見ていると、囲みを跨ぐ・囲みの辺に密着する
といった崩れを見逃す。描いた絵で実際に見つかったのがこれだった。
"""
import pathlib
import re
import sys

PAD = 6.0          # 囲みの内側に最低限ほしい余白
SIZE = {"t": 12.5, "s": 10.5, "mo": 10.5}


def width_of(text, size):
    return sum(size * (1.0 if ord(ch) > 0x2E80 else 0.55) for ch in text)


def boxes(svg):
    out = []
    for m in re.finditer(r"<rect[^>]*>", svg):
        g = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', m.group(0)))
        try:
            x, y = float(g["x"]), float(g["y"])
            w, h = float(g["width"]), float(g["height"])
        except KeyError:
            continue
        out.append((x, y, x + w, y + h, "dasharray" in m.group(0)))
    return out


def texts(svg):
    out = []
    for m in re.finditer(r'<text[^>]*class="([^"]*)"[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*>([^<]*)</text>', svg):
        cls, x, y, body = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4)
        size = SIZE.get(cls.split()[0], 12.0)
        w = width_of(body, size)
        anchored = 'text-anchor="middle"' in m.group(0)
        left = x - w / 2 if anchored else x
        out.append((left, y - size, left + w, y + size * 0.3, body))
    return out


def check(path):
    svg = re.search(r"<svg[\s\S]*?</svg>", pathlib.Path(path).read_text(encoding="utf-8")).group(0)
    rects = boxes(svg)
    frames = [r for r in rects if r[4]]
    faults = []

    def against_frames(l, t, r, b, what):
        for fl, ft, fr, fb, _ in frames:
            inside_x = l >= fl and r <= fr
            overlaps = l < fr and r > fl and t < fb and b > ft
            if not overlaps:
                continue
            if not inside_x or t < ft or b > fb:
                faults.append(f"{what}: 囲み({fl:.0f}-{fr:.0f})を跨ぐ [{l:.0f}-{r:.0f}]")
            elif min(l - fl, fr - r) < PAD:
                faults.append(f"{what}: 囲み({fl:.0f}-{fr:.0f})の辺に密着 余白{min(l-fl, fr-r):.0f}px")

    for l, t, r, b, dashed in rects:
        if not dashed:
            against_frames(l, t, r, b, f"箱[{l:.0f},{t:.0f}]")
    for l, t, r, b, body in texts(svg):
        against_frames(l, t, r, b, f"文字「{body[:12]}」")

    for f in faults:
        print("  ✗", f)
    print(f"  {'崩れなし' if not faults else str(len(faults)) + '件'}")
    return not faults


sys.exit(0 if all([check(p) for p in sys.argv[1:]]) else 1)
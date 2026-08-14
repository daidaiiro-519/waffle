"""記号と線がつながっているかを、座標で確かめる。

目で見て「近い」で済ませると、斜めに入った線と辺に直角な記号のずれを見落とす。
確かめるのは2つ——(1)線の端が記号の先端に一致するか (2)線の最後の一区間が
記号と同じ向きか。どちらかが外れていれば、絵の上で必ず離れて見える。
"""
import math
import re
import sys

LEN = {"one": 6, "exactly-one": 12, "zero-or-one": 24,
       "many": 36, "one-or-more": 48, "zero-or-more": 57, "held": 18}


def _last_seg(d):
    """経路の最後の2点を取り出す。"""
    nums = re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)
    if len(nums) < 2:
        return None
    return [(float(a), float(b)) for a, b in nums[-2:]]


def check(svg, name=""):
    faults = []
    paths = re.findall(r'<path class="wf-edge" d="([^"]+)"', svg)
    syms = re.findall(r'<g class="wf-sym" transform="translate\(([-\d.]+),([-\d.]+)\) '
                      r'rotate\((-?[\d.]+)\)">(.*?)</g>', svg, re.S)
    for sx, sy, sa, body in syms:
        sx, sy, sa = float(sx), float(sy), float(sa)
        kind = next((k for k, v in LEN.items()
                     if _shape_of(body) == k), None) or _shape_of(body)
        L = LEN.get(kind, 12)
        tip = (sx + math.cos(math.radians(sa)) * L,
               sy + math.sin(math.radians(sa)) * L)
        best, bestd = None, 1e9
        for d in paths:
            for end in (_ends(d)):
                dist = math.hypot(end[0][0] - tip[0], end[0][1] - tip[1])
                if dist < bestd:
                    bestd, best = dist, end
        if bestd > 2.0:
            faults.append(f"{name} {kind}: 記号の先端と線の端が {bestd:.1f}px 離れている")
            continue
        (px, py), (qx, qy) = best[0], best[1]
        ang = math.degrees(math.atan2(py - qy, px - qx))
        gap = abs((ang - sa + 180) % 360 - 180)
        if gap > 12:
            faults.append(f"{name} {kind}: 線の向きが記号と {gap:.0f}度 ずれている")
    return faults


def _ends(d):
    nums = [(float(a), float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)]
    if len(nums) < 2:
        return []
    return [(nums[-1], nums[-2]), (nums[0], nums[1])]


def _shape_of(body):
    has_circle = "wf-hollow" in body
    bars = len(re.findall(r"M[\d.-]+,-9 L[\d.-]+,9", body))
    lens_ = "Q18,-18" in body
    if "wf-fill" in body:
        return "held"
    if lens_ and has_circle:
        return "zero-or-more"
    if lens_ and bars:
        return "one-or-more"
    if lens_:
        return "many"
    if has_circle:
        return "zero-or-one"
    return "exactly-one" if bars >= 2 else "one"


if __name__ == "__main__":
    html = open(sys.argv[1], encoding="utf-8").read()
    bad = []
    for m in re.finditer(r"<svg[^>]*>(.*?)</svg>", html, re.S):
        bad += check(m.group(1))
    print("\n".join(bad) if bad else "つながりに欠けは無い")
    sys.exit(1 if bad else 0)
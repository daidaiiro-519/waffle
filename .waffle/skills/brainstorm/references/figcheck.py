"""図の中の文字が、重なっていないか・枠からはみ出していないかを見る。

  python3 figcheck.py <図を持つモジュール名> ...

**目で見つける前に、機械で落とす。**実際に、矢印が箱を貫き、
注記が2つ重なって別の文になっている図を出してしまった。
"""
import importlib
import re
import sys


def check(name, fig):
    svg = fig[0] if isinstance(fig, tuple) else fig
    items = []
    for m in re.finditer(r'<text x="([\d.]+)" y="([\d.]+)"([^>]*)>(.*?)</text>', svg):
        x, y, attr = float(m.group(1)), float(m.group(2)), m.group(3)
        txt = re.sub(r"<[^>]+>", "", m.group(4))
        size = float(re.search(r'font-size="([\d.]+)"', attr).group(1)) if "font-size" in attr else 10
        w = len(txt) * size * 0.85           # 日本語は全角なので、字数 × 字送りで見る
        x0 = x - w / 2 if "middle" in attr else x
        items.append((y, x0, x0 + w, txt))
    vb = [float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups()]
    items.sort()
    bad = [(y, t, t2) for i, (y, a, b, t) in enumerate(items)
           for (y2, a2, b2, t2) in items[i + 1:]
           if abs(y - y2) < 10 and a < b2 - 2 and a2 < b - 2]
    over = [t for (y, a, b, t) in items if b > vb[0] + 2 or y > vb[1]]
    print(f"{name}: 文字 {len(items)} 件 ／ 重なり {len(bad)} 件 ／ はみ出し {len(over)} 件")
    for y, t, t2 in bad:
        print(f"   重なり y={y}: 「{t[:26]}」 × 「{t2[:26]}」")
    for t in over:
        print(f"   はみ出し: 「{t[:40]}」")
    return len(bad) + len(over)


def main() -> int:
    bad = 0
    for mod in sys.argv[1:]:
        m = importlib.import_module(mod)
        for attr in dir(m):
            v = getattr(m, attr)
            if attr.isupper() and isinstance(v, tuple) and v and isinstance(v[0], str) and "<svg" in v[0]:
                bad += check(f"{mod}.{attr}", v)
    print("食い違いは無い" if not bad else f"直すところが {bad} 件ある")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

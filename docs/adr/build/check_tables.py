"""表の見出しとセルの数が合っているかを見る。

2つ取り違えたことがある。
  ・`<thead>` も `<th` に一致する ── 見出しは `<th[ >]` で数える
  ・縦の結合（rowspan）を数えていないと、正しい表を誤報する
"""
from __future__ import annotations

import re
import sys
import pathlib

CELL = re.compile(r"<td([^>]*)>")
SPAN = lambda attrs, name: int((re.search(rf'{name}="(\d+)"', attrs) or [0, 1])[1])


def check(path, verbose: bool = True) -> int:
    s = pathlib.Path(path).read_text(encoding="utf-8")
    bad = 0
    for i, t in enumerate(re.findall(r"<table>.*?</table>", s, re.S), 1):
        parts = t.split("</thead>")
        if len(parts) < 2:          # 見出しの無い表は対象外
            continue
        head = len(re.findall(r"<th[ >]", parts[0]))
        pending: list[list[int]] = []   # [残り行数, 占める列数]
        off = []
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", parts[1], re.S)
        for r in rows:
            carried = sum(p[1] for p in pending)
            here, fresh = 0, []
            for attrs in CELL.findall(r):
                cs = SPAN(attrs, "colspan")
                here += cs
                rs = SPAN(attrs, "rowspan")
                if rs > 1:
                    fresh.append([rs - 1, cs])
            # 減らすのは、この行より前から続いているものだけ。
            # 自分の行でも減らすと、最後の1行を数え落とす
            for p in pending:
                p[0] -= 1
            pending = [p for p in pending if p[0] > 0] + fresh
            n = carried + here
            if n != head:
                off.append(n)
        if verbose:
            print(f"  表{i}: 見出し{head} 行{len(rows)} 列ずれ{off if off else 'なし'}")
        bad += len(off)
    return bad


if __name__ == "__main__":
    total = 0
    for p in sys.argv[1:]:
        print(pathlib.Path(p).name)
        total += check(p)
    print("列ずれ合計:", total)
    raise SystemExit(1 if total else 0)

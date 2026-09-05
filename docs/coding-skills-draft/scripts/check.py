"""規約の形を検証する。

  python3 check.py

見るのは4つ。欄の欠け ・ 出典の空 ・ 置き場所の食い違い ・ 重なり。
**判断はしない。**食い違いを出すだけで、どちらを直すかは人が決める。
"""
from __future__ import annotations

import re
import sys

from _common import load_all, rule_ids

REQUIRED_FRONT = ["id", "layer", "category", "declares", "updated"]
REQUIRED_SECTIONS = ["概要", "適用範囲外", "委譲する判断", "出典"]
UNFILLED = re.compile(r"《[^》]*》")


def main() -> int:
    specs = load_all()
    problems: list[str] = []

    for s in specs:
        where = s.path.relative_to(s.path.parents[2])

        for key in REQUIRED_FRONT:
            if not s.front.get(key):
                problems.append(f"{where}: 前置きに {key} が無い")
        if not s.axes:
            problems.append(f"{where}: 依存する軸が宣言されていない")

        for name in REQUIRED_SECTIONS:
            if name not in s.sections:
                problems.append(f"{where}: 「{name}」の節が無い")

        if s.axes and s.dir_axes and s.axes != s.dir_axes:
            problems.append(
                f"{where}: 置き場所と宣言した軸が食い違う "
                f"（ディレクトリ {s.dir_axes} ／ 前置き {s.axes}）")

        unfilled = UNFILLED.findall(s.body)
        if unfilled:
            problems.append(
                f"{where}: 埋めていない箇所が {len(unfilled)} 件 "
                f"（例: {unfilled[0]}）")

        if "出典" in s.sections:
            tail = s.body.split("## 出典", 1)[1]
            if "未照合" in tail or "未取得" in tail:
                problems.append(f"{where}: 出典が原文と照合されていない")

    # 同じ層で、同じ ID が2度使われていないか
    seen: dict[tuple[str, str], str] = {}
    for s in specs:
        for rid in rule_ids(s):
            key = (s.layer, rid)
            if key in seen:
                problems.append(
                    f"{s.layer}: ID {rid} が {seen[key]} と {s.kind}.md で重なる")
            seen[key] = f"{s.kind}.md"

    print(f"規約 {len(specs)} 本を検証した")
    if not problems:
        print("食い違いは無い")
        return 0
    print(f"\n食い違い {len(problems)} 件")
    for p in problems:
        print(f"  {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

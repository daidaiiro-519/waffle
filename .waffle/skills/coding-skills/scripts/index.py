"""人が読む索引を作り直す。

  python3 index.py            constraints/INDEX.md を書き出す
  python3 index.py --stdout   書き出さずに表示する

**索引は生成物である。**手で書き換えても、次の生成で消える。
"""
from __future__ import annotations

import argparse
import sys

from _common import CONSTRAINTS, load_all, rule_ids

HEAD = """<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->
# 規約の索引

## 概要

**この索引は生成物である。**
規約を足したら作り直す。手で書いた行は、次の生成で消える。

"""


def render(specs) -> str:
    out = [HEAD]

    out.append("## 層ごとの規約\n\n")
    out.append("| 層 | 依存する軸 | 規約 | 宣言すること | 規則 |\n|---|---|---|---|---|\n")
    for s in specs:
        axes = " ／ ".join(f"{k}＝{v}" for k, v in s.axes.items()) or "**宣言なし**"
        ids = rule_ids(s)
        out.append(f"| `{s.layer}` | {axes} | `{s.kind}.md` | "
                   f"{s.front.get('declares','')} | {len(ids) or '─'} |\n")

    out.append("\n## 種別ごとの規約\n\n")
    by_cat: dict[str, list] = {}
    for s in specs:
        by_cat.setdefault(s.front.get("category", "（無し）"), []).append(s)
    out.append("| 種別 | 規約 |\n|---|---|\n")
    for cat in sorted(by_cat):
        items = " ・ ".join(f"`{s.layer}/{s.kind}.md`" for s in by_cat[cat])
        out.append(f"| {cat} | {items} |\n")

    out.append("\n## 数\n\n")
    out.append("| 数えたもの | 件数 |\n|---|---|\n")
    out.append(f"| 規約 | {len(specs)} 本 |\n")
    out.append(f"| 層 | {len({s.layer for s in specs})} |\n")
    out.append(f"| 規則 | {sum(len(rule_ids(s)) for s in specs)} 件 |\n")
    return "".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="規約の索引を作り直す")
    p.add_argument("--stdout", action="store_true")
    args = p.parse_args()

    specs = load_all()
    text = render(specs)
    if args.stdout:
        print(text)
        return 0
    target = CONSTRAINTS / "INDEX.md"
    target.write_text(text, encoding="utf-8")
    print(f"{target} を作り直した（規約 {len(specs)} 本）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

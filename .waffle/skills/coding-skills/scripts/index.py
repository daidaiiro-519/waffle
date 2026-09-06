"""人が読む索引を作り直す。

  python3 index.py            constraints/INDEX.md を書き出す
  python3 index.py --stdout   書き出さずに表示する

**索引は生成物である。**手で書き換えても、次の生成で消える。
"""
from __future__ import annotations

import argparse
import re
import sys

from _common import CONSTRAINTS, REFERENCES, SOURCES, load_all

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
        ids = s.rule_ids
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

    out.append("\n" + counts(specs))
    return "".join(out)


def counts(specs) -> str:
    """数は導出物である。参照文書の本文へ手で書かず、ここが書き出す。"""
    from _common import sections, tables
    rows, used = [], set()
    for s in specs:
        for tb in tables(sections(s.body).get("出典", "")):
            if not tb.has("原典"):
                continue
            for r in tb.rows:
                rows.append(r)
                m = re.search(r"https?://\S+", r["原典"])
                if m:
                    used.add(m.group(0))
    unsourced = sum(1 for s in specs for r in s.rule_ids if r not in s.sourced_ids)
    approved = sum(1 for s in specs if s.front.get("approved_by"))
    files = [p for p in SOURCES.iterdir() if p.is_file() and not p.name.endswith(".meta.json")]
    return ("## 数\n\n"
            "<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->\n\n"
            "| 数えたもの | 件数 |\n|---|---|\n"
            f"| 規約 | {len(specs)} 本 |\n"
            f"| 層 | {len({s.layer for s in specs})} |\n"
            f"| 規則 | {sum(len(s.rule_ids) for s in specs)} 件 |\n"
            f"| 出典を持たない規則 | {unsourced} 件 |\n"
            f"| 出典の行 | {len(rows)} 行 |\n"
            f"| 出典が指す原典 | {len(used)} 本 |\n"
            f"| 落としてある原典 | {len(files)} 本 |\n"
            f"| 承認が記録された規約 | {approved} / {len(specs)} 本 |\n")


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

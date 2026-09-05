"""規約の形を検証する。

  python3 check.py

見るのは5つ。欄の欠け ・ 雛形との食い違い ・ 出典の空 ・ 置き場所の食い違い ・ 重なり。
**判断はしない。**食い違いを出すだけで、どちらを直すかは人が決める。
"""
from __future__ import annotations

import re
import sys

from _common import load_all, local_source, rule_ids, source_rows

REQUIRED_FRONT = ["id", "layer", "category", "declares", "updated"]
REQUIRED_SECTIONS = ["概要", "適用範囲外", "委譲する判断", "出典"]
UNFILLED = re.compile(r"《[^》]*》")
HEADING = re.compile(r"^## (.+)$", re.M)


def template_sections(root, kind: str) -> list[str]:
    """種類に対応する雛形の節を返す。雛形が無ければ空を返す。"""
    path = root / "templates" / f"{kind}.md"
    if not path.exists():
        return []
    return HEADING.findall(path.read_text(encoding="utf-8"))


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

        # 雛形は、その種類の規約が必ず持つ節を定める。足す分は規約の自由にする
        root = s.path.parents[2]
        wanted = template_sections(root, s.path.stem)
        if not wanted:
            problems.append(f"{where}: 種類 {s.path.stem} の雛形が無い")
        for name in wanted:
            if name not in s.sections:
                problems.append(f"{where}: 雛形にある「{name}」の節が無い")

        # ディレクトリに現れない軸は、同じ層の規約が provides で与えているものだけ許す
        provided = {}
        for other in specs:
            if other.layer == s.layer:
                provided.update(other.provides)
        for axis, value in s.axes.items():
            if s.dir_axes.get(axis) == value:
                continue
            if provided.get(axis) == value:
                continue
            problems.append(
                f"{where}: 軸 {axis}＝{value} が、置き場所にも provides にも無い")
        for axis, value in s.dir_axes.items():
            if s.axes.get(axis) != value:
                problems.append(
                    f"{where}: 置き場所の軸 {axis}＝{value} が、前置きに無い")

        unfilled = UNFILLED.findall(s.body)
        if unfilled:
            problems.append(
                f"{where}: 埋めていない箇所が {len(unfilled)} 件 "
                f"（例: {unfilled[0]}）")

        if "出典" in s.sections:
            tail = s.body.split("## 出典", 1)[1]
            if "未照合" in tail or "未取得" in tail:
                problems.append(f"{where}: 出典が原文と照合されていない")
            # 出典の URL に、照合する文字列が本当に在るか
            for url, needle in source_rows(s):
                body = local_source(url)
                if body is None:
                    problems.append(f"{where}: 出典の原文を落としていない（{url}）")
                    continue
                text = body.read_text(encoding="utf-8", errors="replace")
                if needle not in text:
                    problems.append(
                        f"{where}: 照合する文字列 `{needle}` が、"
                        f"その原文に無い（{url}）")

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

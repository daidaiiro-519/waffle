"""軸の値を受け取り、合致する規約を集める。

  python3 collect.py --lang rust --purpose hook

**0件の層も、0件として出す。**「無い」ことが見えなければ、
足りないことに気づけない。
"""
from __future__ import annotations

import argparse
import sys

from _common import KINDS_BY_SHAPE, load_all, rule_ids, shape_of


def matches(spec_axes: dict, given: dict) -> bool:
    """規約が宣言した軸が、渡された値にすべて含まれるかを見る。

    宣言した軸が1つでも渡されていない、または値が違えば、その規約は効かない。
    """
    if not spec_axes:
        return False
    return all(given.get(axis) == value for axis, value in spec_axes.items())


def main() -> int:
    p = argparse.ArgumentParser(description="軸の値に合致する規約を集める")
    p.add_argument("--lang")
    p.add_argument("--arch")
    p.add_argument("--purpose")
    p.add_argument("--runtime")
    args = p.parse_args()

    given = {k: v for k, v in {
        "language": args.lang, "architecture": args.arch,
        "purpose": args.purpose, "runtime": args.runtime}.items() if v}
    if not given:
        p.error("軸の値を1つ以上渡してください")

    specs = load_all()

    # 1段目。渡された軸だけで集める
    hit = [s for s in specs if matches(s.axes, given)]

    # 2段目。用途の規約が指定した軸を足して、集め直す
    derived = {}
    for s in hit:
        for axis, value in s.provides.items():
            if axis not in given:
                derived[axis] = (value, s.path.name)
    if derived:
        given.update({a: v for a, (v, _) in derived.items()})
        hit = [s for s in specs if matches(s.axes, given)]

    print("渡された軸")
    for axis, value in given.items():
        src = derived.get(axis)
        note = f"（{src[1]} が指定）" if src else ""
        print(f"  {axis} = {value}{note}")

    print(f"\n集まった規約 {len(hit)} 本")
    by_layer: dict[str, list] = {}
    for s in hit:
        by_layer.setdefault(s.layer, []).append(s)
    for layer in sorted(by_layer):
        print(f"  {layer}/")
        for s in sorted(by_layer[layer], key=lambda x: x.kind):
            ids = rule_ids(s)
            tail = f"　規則 {len(ids)} 件" if ids else ""
            print(f"    {s.kind}.md　{s.front.get('declares','')}{tail}")

    # この場面で埋まっているべき層と、その中で欠けている種類を出す
    wanted = []
    if args.lang:
        wanted.append(f"lang.{args.lang}")
    arch = given.get("architecture")
    if arch:
        wanted.append(f"arch.{arch}")
    if args.lang and arch:
        wanted.append(f"lang.{args.lang}+arch.{arch}")
    if args.purpose:
        wanted.append(f"purpose.{args.purpose}")

    lacks: list[str] = []
    for layer in wanted:
        have = {s.kind for s in hit if s.layer == layer}
        for kind in KINDS_BY_SHAPE[shape_of(layer)]:
            if kind not in have:
                lacks.append(f"{layer}/{kind}.md")

    print(f"\n足りない規約 {len(lacks)} 本")
    for m in lacks:
        print(f"  {m}　── 書かれていない")

    if lacks:
        print("\n書かずに止まること。references/authoring.md へ回り、"
              "承認を経てから集め直す")
        return 1
    if not hit:
        print("\n合致する規約が無い。書く前に、作る手順へ回ること")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

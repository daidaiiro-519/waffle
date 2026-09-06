"""規約の形を検証する。

  python3 check.py              食い違いを出す
  python3 check.py --contracts  検査と、それが守っている宣言の一覧を出す

**検査は、守っている宣言を出典として持つ。**
規則に出典を求めるなら、検査にも同じものを求める ──
`declared_in` が原典、`needle` がその宣言の一文に当たる。
検査を1つも走らせる前に、全ての `needle` が実在するかを確かめ、
無ければそこで落ちる。宣言を消せば、その検査が落ちて気づける。

**対象は、保守し続けるものだけである。**
`constraints/` ・ `references/` ・ `templates/` を見る。
`sources/` は原典なので見ない ── 変えないものに契約を課すと、原典が保守対象になる。
`scripts/` は振る舞いを持つので、文言の照合では裁けない（`tests/` が見る）。

**判断はしない。**食い違いを出すだけで、どちらを直すかは人が決める。
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import Callable

from _common import (ID_COLUMN, REFERENCES, ROOT, SOURCE_SECTION, Spec, kinds_by_shape,
                     load_all, load_templates, sections, shape_of, tables)

REQUIRED_FRONT = ["id", "layer", "category", "declares", "updated",
                  "approved_by", "approved_at"]
REQUIRED_SECTIONS = ["概要", "適用範囲外", "委譲する判断", "出典"]
UNFILLED = re.compile(r"《[^》]*》")

# 機械では裁けない宣言。人が見るものとして、ここに並べておく
# ── 「検査が無い」ことと「検査できない」ことを、読み手が区別できるようにする
KINDS = {"規格", "文献", "実測"}

HUMAN_ONLY = [
    ("同じ層の2本が反対のことを言っていないか", "SKILL.md Step 3"),
    ("委譲すると宣言していない点を、下の層が特殊化していないか", "SKILL.md Step 3"),
    ("出典の原典が、その規則を実際に裏づけているか", "references/sources.md 原典の読み方"),
]


@dataclass
class Check:
    """検査1つ。守っている宣言を必ず持つ。"""
    name: str
    target: str          # constraints / references / templates
    declared_in: str     # その宣言が在るファイル（ルートからの相対）
    needle: str          # そのファイルに実在する、宣言の文字列
    run: Callable[[list[Spec]], list[str]]


CHECKS: list[Check] = []


def check(name, target, declared_in, needle):
    def deco(fn):
        CHECKS.append(Check(name, target, declared_in, needle, fn))
        return fn
    return deco


# ── 検査 ──────────────────────────────────────────────────────

@check("前置きの欄が揃っている", "constraints",
       "references/authoring.md", "埋まらない欄が残るなら、まだ規約になっていない")
def _front(specs):
    return [f"{s.where}: 前置きに {k} が無い"
            for s in specs for k in REQUIRED_FRONT if not s.front.get(k)]


@check("承認が記録されている", "constraints",
       "references/authoring.md", "承認を経てから、正本へ置く")
def _approved(specs):
    return [f"{s.where}: 承認が記録されていない"
            for s in specs if not (s.front.get("approved_by") and s.front.get("approved_at"))]


@check("依存する軸が宣言されている", "constraints",
       "references/axes.md", "層とは、その規約が依存する軸の集合である")
def _axes(specs):
    return [f"{s.where}: 依存する軸が宣言されていない" for s in specs if not s.axes]


@check("宣言した軸と、置き場所が一致する", "constraints",
       "references/authoring.md", "依存する軸の集合が、そのまま置き場所（層）になる")
def _placement(specs):
    out = []
    for s in specs:
        provided = {}
        for other in specs:
            if other.layer == s.layer:
                provided.update(other.provides)
        for axis, value in s.axes.items():
            if s.dir_axes.get(axis) != value and provided.get(axis) != value:
                out.append(f"{s.where}: 軸 {axis}＝{value} が、置き場所にも provides にも無い")
        for axis, value in s.dir_axes.items():
            if s.axes.get(axis) != value:
                out.append(f"{s.where}: 置き場所の軸 {axis}＝{value} が、前置きに無い")
    return out


@check("埋めていない箇所が無い", "constraints",
       "references/authoring.md", "埋まらない欄が残るなら、まだ規約になっていない")
def _unfilled(specs):
    out = []
    for s in specs:
        left = UNFILLED.findall(s.body)
        if left:
            out.append(f"{s.where}: 埋めていない箇所が {len(left)} 件（例: {left[0]}）")
    return out


@check("層に、その形が必ず持つ種類が揃っている", "constraints",
       "references/file-catalog.md", "規約の種類1つに、雛形1つが対応する")
def _kinds(specs):
    by_shape, out = kinds_by_shape(), []
    for layer in sorted({s.layer for s in specs}):
        shape = shape_of(layer)
        if not shape:
            out.append(f"{layer}/: 層の名前から形を決められない")
            continue
        if shape not in by_shape:
            out.append(f"{layer}/: file-catalog.md に「{shape}」の行が無い")
            continue
        have = {s.kind for s in specs if s.layer == layer}
        out += [f"{layer}/: {k}.md が無い（{shape}の層が必ず持つ種類）"
                for k in by_shape[shape] if k not in have]
    return out


@check("雛形が定める節を持つ", "templates",
       "references/file-catalog.md", "規約の種類1つに、雛形1つが対応する")
def _sections(specs):
    tpl, out = load_templates(), []
    for s in specs:
        for name in REQUIRED_SECTIONS:
            if name not in s.sections:
                out.append(f"{s.where}: 「{name}」の節が無い")
        if s.kind not in tpl:
            out.append(f"{s.where}: 種類 {s.kind} の雛形が無い")
            continue
        for name in sections(tpl[s.kind]):
            if name not in s.sections:
                out.append(f"{s.where}: 雛形にある「{name}」の節が無い")
    return out


@check("出典の表が、雛形の定める列を持つ", "templates",
       "references/file-catalog.md", "規約の種類1つに、雛形1つが対応する")
def _columns(specs):
    """1列目は「何を裏づけるか」を指すので、種類ごとに違ってよい（規則なら ID）。
    残りの列は出典の形そのものなので、雛形が定めたとおりでなければならない。"""
    tpl, out = load_templates(), []
    for s in specs:
        if s.kind not in tpl:
            continue
        want = [set(t.columns[1:]) for t in tables(sections(tpl[s.kind]).get("出典", ""))]
        if not want:
            continue
        need = want[0]
        for tb in tables(sections(s.body).get("出典", "")):
            missing = need - set(tb.columns)
            if missing:
                out.append(f"{s.where}: 出典の表に {'・'.join(sorted(missing))} の列が無い"
                           f"（雛形 {s.kind}.md が定めている）")
    return out


@check("規則が、出典の行を持つ", "constraints",
       "SKILL.md", "出典を持たないものは規則ではない")
def _sourced(specs):
    return [f"{s.where}: 規則 {r} に出典が無い"
            for s in specs for r in s.rule_ids if r not in s.sourced_ids]


@check("出典の行が、実在する規則を指している", "constraints",
       "SKILL.md", "出典を持たないものは規則ではない")
def _ghost(specs):
    return [f"{s.where}: 出典の行 {r} に、対応する規則が無い"
            for s in specs for r in sorted(s.sourced_ids - set(s.rule_ids))]


@check("同じ層で、規則の ID が重ならない", "constraints",
       "references/glossary.md", "同じ層の中で、ID は重ならない")
def _unique(specs):
    seen, out = {}, []
    for s in specs:
        for rid in s.rule_ids:
            if (s.layer, rid) in seen:
                out.append(f"{s.layer}: ID {rid} が {seen[(s.layer, rid)]} と {s.kind}.md で重なる")
            seen[(s.layer, rid)] = f"{s.kind}.md"
    return out


@check("詳細の塊が、芯と種類ごとの欄を持つ", "templates",
       "templates/rule-core.md", "規則1件は、詳細の塊1つである")
def _blocks(specs):
    """芯は rule-core.md、種類ごとの欄は種別の雛形が宣言する。写しを持たない。"""
    import relist
    core = [r["何"] for tb in tables(sections(load_templates()["rule-core"]).get("芯", ""))
            for r in tb.rows if "塊の表" in r.get("どこに書くか", "")]
    tpl = load_templates()
    out = []
    for s in specs:
        if not relist.shape(s.kind):
            continue
        want = set(core)
        for name, body in sections(tpl[s.kind]).items():
            if "### 《" not in body:      # 詳細の塊を示す節だけを見る
                continue
            for tb in tables(body):
                if tb.columns[:2] == ["項目", "内容"]:
                    want |= {r["項目"] for r in tb.rows}
        for rid, _, fields in relist.details(s.body):
            missing = sorted(want - set(fields))
            if missing:
                out.append(f"{s.where}: {rid} に {' ・ '.join(missing)} が無い")
    return out


@check("一覧が、詳細から導出したものと一致する", "constraints",
       "references/glossary.md", "数は導出物である")
def _relist(specs):
    """一覧は写しである。写しを守る検査ではなく、写しを作らないことで揃える。"""
    import relist
    out = []
    for s in specs:
        table = relist.table_for(s)
        if table and relist.apply(s, table) is not None:
            out.append(f"{s.where}: 一覧が詳細と食い違う"
                       f"（python3 scripts/relist.py で書き直す）")
    return out


@check("出典の種類が、認める3つのいずれかである", "constraints",
       "references/sources.md", "## 認める出典")
def _kinds(specs):
    """語彙の揺らぎはノイズである。認めた値の集合に収まっているかは形の検査。"""
    out = []
    for s in specs:
        for tb in tables(sections(s.body).get(SOURCE_SECTION, "")):
            if not tb.has("種類"):
                continue
            for r in tb.rows:
                if r["種類"] not in KINDS:
                    out.append(f"{s.where}: 出典の種類 {r['種類']} は認めていない"
                               f"（{' ・ '.join(sorted(KINDS))}）")
    return out


@check("参照文書が指すファイルが実在する", "references",
       "references/file-catalog.md", "参照するもの")
def _refs(specs):
    out = []
    for tb in tables((REFERENCES / "file-catalog.md").read_text(encoding="utf-8")):
        if not tb.has("ファイル"):
            continue
        for row in tb.rows:
            name = row["ファイル"].strip("`")
            if "/" not in name and not name.endswith(".md"):
                continue
            if not (ROOT / name).exists():
                out.append(f"references/file-catalog.md: {name} が無い")
    return out


@check("参照文書に、手で書いた数が残っていない", "references",
       "references/glossary.md", "参照文書の本文へ手で書かない")
def _counts(specs):
    out = []
    for path in sorted(REFERENCES.glob("*.md")):
        for m in re.finditer(r"^\|[^|]*\|\s*\**(\d+)\s*(件|本|行)\**\s*\|",
                             path.read_text(encoding="utf-8"), re.M):
            out.append(f"references/{path.name}: 表に数が手で書かれている"
                       f"（{m.group(1)} {m.group(2)}）── index.py が書き出す")
    return out


# ── 走らせる ──────────────────────────────────────────────────

def verify_contracts() -> list[str]:
    """検査より先に、検査が守っている宣言が実在するかを確かめる。"""
    out = []
    for c in CHECKS:
        path = ROOT / c.declared_in
        if not path.exists():
            out.append(f"検査「{c.name}」: 宣言のあるはずの {c.declared_in} が無い")
        elif c.needle not in path.read_text(encoding="utf-8"):
            out.append(f"検査「{c.name}」: 守っている宣言が {c.declared_in} に見つからない"
                       f"（{c.needle}）")
    return out


def show_contracts() -> int:
    print(f"検査 {len(CHECKS)} 件。それぞれが守っている宣言を持つ\n")
    for target in ["constraints", "references", "templates"]:
        print(f"[{target}]")
        for c in CHECKS:
            if c.target == target:
                print(f"  {c.name}\n      ← {c.declared_in}: {c.needle}")
        print()
    print("[機械では裁けない ── 人が見る]")
    for what, where in HUMAN_ONLY:
        print(f"  {what}\n      ← {where}")
    print("\n[対象外]")
    print("  sources/  原典なので契約を持たない")
    print("  scripts/  振る舞いを持つ。tests/ が見る")
    return 0


def main() -> int:
    if "--contracts" in sys.argv:
        return show_contracts()

    broken = verify_contracts()
    if broken:
        print("検査を走らせる前に止まった ── 検査が守っている宣言が見つからない\n")
        for b in broken:
            print(f"  {b}")
        return 2

    specs = load_all()
    problems = [p for c in CHECKS for p in c.run(specs)]

    print(f"規約 {len(specs)} 本を、検査 {len(CHECKS)} 件で検証した")
    if not problems:
        print("食い違いは無い")
        return 0
    print(f"\n食い違い {len(problems)} 件")
    for p in sorted(problems):
        print(f"  {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

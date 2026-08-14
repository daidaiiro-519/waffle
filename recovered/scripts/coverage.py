"""受け入れ基準のうち、対応する筋書きを持たないものを数える。

規約自身が「筋書きの無い基準は、誰も検証していません」と述べている。
検査はこれを見ないので、手で数える。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = pathlib.Path(CWD) / ".waffle/documents/specs/bc-artifact-share"


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value")
    except Exception:
        return None


total_criteria = uncovered = 0
report = []

for p in sorted(SPECS.rglob("uc-*.json")):
    rel = str(p.relative_to(CWD))
    name = p.stem
    criteria = q(rel, "acceptanceCriteria", "items") or []
    scenarios = q(rel, "acceptanceScenarios", "scenarios") or []
    covered = {s.get("covers", "") for s in scenarios}
    # covers は基準の文言をそのまま指す。前置きが付く書き方もある
    missing = [c for c in criteria
               if not any(c in cv or cv in c for cv in covered if cv)]
    total_criteria += len(criteria)
    uncovered += len(missing)
    if missing:
        report.append((name, len(criteria), missing))

print(f"受け入れ基準 {total_criteria} 件のうち、筋書きを持たないもの {uncovered} 件\n")
for name, n, missing in report:
    print(f"■ {name}（基準{n}件中 {len(missing)}件）")
    for m in missing:
        print(f"    - {m}")

# 操作保証の側も同じことを見る
print()
total_g = uncovered_g = 0
for p in sorted(SPECS.rglob("uc-*.json")):
    rel = str(p.relative_to(CWD))
    guarantees = q(rel, "operationGuarantees", "items") or []
    gscen = q(rel, "guaranteeScenarios", "scenarios") or []
    total_g += len(guarantees)
    # 保証の筋書きは covers を持たない書き方が多いので、件数だけ突き合わせる
    if len(gscen) < len(guarantees):
        uncovered_g += len(guarantees) - len(gscen)
        print(f"■ {p.stem}: 操作保証{len(guarantees)}件に対し筋書き{len(gscen)}件")
print(f"\n操作保証 {total_g} 件、筋書きが足りない分 {uncovered_g} 件")

"""受け入れ条件と振る舞いの筋書きが、1対1に収まるかを調べる。

件数の大小は、多対多が起きているかの構造的な手がかりになる。
筋書きが条件より多ければ、1つの条件に複数の筋書きが要る例がある。
筋書きが少なければ、1つの筋書きが複数を満たしているか、単に欠けている。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = pathlib.Path(CWD) / ".waffle/documents/specs"


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        v = json.loads(r.stdout).get("value")
    except Exception:
        return []
    return v or []


def rel(p: pathlib.Path) -> str:
    return str(p.relative_to(CWD))


rows = []
for p in sorted(SPECS.rglob("uc-*.json")):
    c = len(q(rel(p), "acceptanceCriteria", "items"))
    s = len(q(rel(p), "acceptanceScenarios", "scenarios"))
    g = len(q(rel(p), "operationGuarantees", "items"))
    gs = len(q(rel(p), "guaranteeScenarios", "scenarios"))
    rows.append(("uc", p.stem, c, s, g, gs))

for p in sorted(SPECS.rglob("agg-*.json")):
    c = len(q(rel(p), "invariants", "items"))
    s = len(q(rel(p), "invariantScenarios", "scenarios"))
    rows.append(("agg", p.stem, c, s, 0, 0))

more = [r for r in rows if r[3] > r[2]]
less = [r for r in rows if r[3] < r[2]]
same = [r for r in rows if r[3] == r[2]]

print(f"{'種別':4} {'仕様':34} {'条件':>4} {'筋書き':>5}  {'保証':>4} {'保証筋書き':>6}")
for kind, name, c, s, g, gs in rows:
    mark = "  筋書きが多い" if s > c else ("  筋書きが少ない" if s < c else "")
    print(f"{kind:4} {name:34} {c:4} {s:5}  {g:4} {gs:6}{mark}")

print()
print(f"筋書きの方が多い: {len(more)} 仕様  →  1条件に複数の筋書きが要る例がある")
print(f"同数            : {len(same)} 仕様")
print(f"筋書きの方が少ない: {len(less)} 仕様  →  欠けか、1筋書きが複数条件を満たしている")
print()
print("合計  条件", sum(r[2] for r in rows), "/ 筋書き", sum(r[3] for r in rows))

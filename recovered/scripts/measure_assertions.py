"""筋書きが複数の条件を満たしうるかを、Then の数から測る。

Then が1つだけの筋書きは、複数の条件を同時に満たしているとは考えにくい。
Then が複数ある筋書きだけが、多対1の候補になる。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = pathlib.Path(CWD) / ".waffle/documents/specs"
BLOCKS = ("acceptanceScenarios", "invariantScenarios", "domainServiceScenarios")


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value") or []
    except Exception:
        return []


def assertions(gherkin: str) -> int:
    """Then とそれに続く And を、確かめている事柄の数として数える。"""
    n, in_then = 0, False
    for raw in gherkin.splitlines():
        line = raw.strip()
        if line.startswith("Then"):
            n, in_then = n + 1, True
        elif line.startswith("And") and in_then:
            n += 1
        elif line.startswith(("Given", "When", "Scenario")):
            in_then = False
    return n


rows = []
for p in sorted(SPECS.rglob("*.json")):
    rel = str(p.relative_to(CWD))
    for b in BLOCKS:
        for s in q(rel, b, "scenarios[].{n:name,g:gherkin}"):
            rows.append((p.stem, b, s["n"], assertions(s.get("g") or "")))

total = len(rows)
single = [r for r in rows if r[3] <= 1]
multi = [r for r in rows if r[3] >= 2]
big = [r for r in rows if r[3] >= 3]

print(f"筋書き 合計 {total} 件")
print(f"  確かめている事柄が1つ : {len(single)} 件 ({len(single)*100//total}%)  → 多対1になりえない")
print(f"  2つ以上              : {len(multi)} 件 ({len(multi)*100//total}%)  → 多対1の候補")
print(f"  3つ以上              : {len(big)} 件")
print()
print("確かめている事柄が多い順（上位12件）")
for name, b, n, c in sorted(rows, key=lambda r: -r[3])[:12]:
    print(f"  {c:2}  [{name}] {n}")

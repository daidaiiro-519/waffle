"""仕様ごとに、要件の数と筋書きの数を並べる。

文言の照合には頼らない。筋書きの方が少ない仕様だけが、本当に足りていない
可能性のある場所になる。
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
        return json.loads(r.stdout).get("value") or []
    except Exception:
        return []


rows = []
for p in sorted(SPECS.rglob("uc-*.json")):
    rel = str(p.relative_to(CWD))
    c = len(q(rel, "acceptanceCriteria", "items"))
    s = len(q(rel, "acceptanceScenarios", "scenarios"))
    g = len(q(rel, "operationGuarantees", "items"))
    gs = len(q(rel, "guaranteeScenarios", "scenarios"))
    rows.append((p.stem, c, s, g, gs))

print(f"{'仕様':32} 受入基準 筋書き   保証 保証筋書き")
short = []
for name, c, s, g, gs in rows:
    mark = ""
    if s < c or gs < g:
        mark = "  ← 筋書きの方が少ない"
        short.append((name, c, s, g, gs))
    print(f"{name:32} {c:6} {s:6} {g:6} {gs:6}{mark}")

print(f"\n合計: 受入基準 {sum(r[1] for r in rows)} / 筋書き {sum(r[2] for r in rows)}"
      f" ・ 操作保証 {sum(r[3] for r in rows)} / 保証筋書き {sum(r[4] for r in rows)}")
print(f"筋書きの方が少ない仕様: {len(short)} 件")

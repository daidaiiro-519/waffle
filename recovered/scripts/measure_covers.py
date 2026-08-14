"""対応欄（covers）の記入率を、全文書・全ブロックで測る。

これまで「3分の1」と述べてきたが、それは集約1文書の値だった可能性がある。
"""
from __future__ import annotations

import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = pathlib.Path(CWD) / ".waffle/documents/specs"
BLOCKS = ("acceptanceScenarios", "guaranteeScenarios",
          "invariantScenarios", "domainServiceScenarios")


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value") or []
    except Exception:
        return []


tally = {b: [0, 0] for b in BLOCKS}
samples = []
for p in sorted(SPECS.rglob("*.json")):
    rel = str(p.relative_to(CWD))
    for b in BLOCKS:
        for s in q(rel, b, "scenarios[].{n:name,c:covers}"):
            tally[b][1] += 1
            c = (s.get("c") or "").strip()
            if c:
                tally[b][0] += 1
                if len(samples) < 6:
                    samples.append((p.stem, b, s["n"], c))

print(f"{'ブロック':24} {'記入':>5} {'全体':>5}  記入率")
tot = [0, 0]
for b, (f, t) in tally.items():
    tot[0] += f
    tot[1] += t
    print(f"{b:24} {f:5} {t:5}  {f*100//t if t else 0}%")
print(f"{'合計':24} {tot[0]:5} {tot[1]:5}  {tot[0]*100//tot[1]}%")
print()
print("記入されている値の実例")
for name, b, n, c in samples:
    print(f"  [{name}/{b}]")
    print(f"    筋書き: {n}")
    print(f"    対応欄: {c}")

"""筋書きの方が少ない11仕様について、要件と筋書きの対応を並べて出す。

文字列で判定せず、人が読んで判断するための材料として並べる。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

CWD = "/home/daidaiiro/workspace/waffle"
UC = pathlib.Path(CWD) / ".waffle/documents/specs/bc-artifact-share/subdomain/sd-artifact-sharing/usecase"


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value") or []
    except Exception:
        return []


for name in sys.argv[1:]:
    rel = str((UC / f"{name}.json").relative_to(CWD))
    print(f"\n{'=' * 8} {name}")
    print("--- 受け入れ基準")
    for i, c in enumerate(q(rel, "acceptanceCriteria", "items")):
        print(f"  [{i}] {c}")
    print("--- 筋書きが指している先")
    for s in q(rel, "acceptanceScenarios", "scenarios"):
        print(f"  ・{s['name']}\n      → {s.get('covers', '(無し)')}")
    g = q(rel, "operationGuarantees", "items")
    gs = q(rel, "guaranteeScenarios", "scenarios")
    if len(gs) < len(g):
        print("--- 操作保証")
        for i, x in enumerate(g):
            print(f"  [{i}] {x}")
        print("--- 保証の筋書き")
        for s in gs:
            print(f"  ・{s['name']}")

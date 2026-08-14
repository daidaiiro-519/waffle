"""操作保証と、突き合わせに要る周辺（errors・基準・集約の不変条件）を取り出す。"""
from __future__ import annotations

import glob
import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"
OUT = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/guarantees_dump." + "json")


def q(p, b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value")
    except Exception:
        return None


def texts(items):
    return [(x if isinstance(x, str) else x.get("text", "")) for x in (items or [])]


data = {"usecases": {}, "aggregates": {}}

for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/usecase/uc-*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    g = q(rel, "operationGuarantees", "items")
    if not g:
        continue
    name = rel.split("/")[-1][:-5]
    data["usecases"][name] = {
        "path": rel,
        "bc": "bc-artifact-share" if "bc-artifact-share" in rel else "bc-waffle",
        "guarantees": g,
        "guaranteeScenarios": [s.get("name") for s in (q(rel, "guaranteeScenarios", "scenarios") or [])],
        "errorCodes": q(rel, "errors", "items[].code") or [],
        "criteria": texts(q(rel, "acceptanceCriteria", "items")),
    }

for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/aggregate/agg-*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    name = rel.split("/")[-1][:-5]
    inv = q(rel, "invariants", "items") or []
    data["aggregates"][name] = [(x if isinstance(x, str) else (x.get("rule") or x.get("text", "")))
                                for x in inv]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

ng = sum(len(v["guarantees"]) for v in data["usecases"].values())
print(f"業務ユースケース {len(data['usecases'])} 件 / 保証 {ng} 件")
print(f"集約 {len(data['aggregates'])} 件 / 不変条件 "
      f"{sum(len(v) for v in data['aggregates'].values())} 件")
print("→", OUT)

"""v9/v10 の文書に、廃止した covers が残っていないかを見る。"""
from __future__ import annotations

import glob
import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"
BLOCKS = ("acceptanceScenarios", "guaranteeScenarios")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/bc-waffle/**/*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    name = rel.split("/")[-1][:-5]
    for b in BLOCKS:
        try:
            v = json.loads(run("query", "--operation", "query_path", "--path", rel,
                               "--blockKey", b, "--expression", "scenarios"))["value"]
        except Exception:
            continue
        if not v:
            continue
        n_cov = sum(1 for s in v if "covers" in s)
        n_sat = sum(1 for s in v if "satisfies" in s)
        if n_cov:
            print(f"  {name:38} {b:20} covers={n_cov} satisfies={n_sat}")

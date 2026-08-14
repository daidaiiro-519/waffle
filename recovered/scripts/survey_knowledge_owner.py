"""knowledge が誰のものとして宣言されているかを数える。"""
from __future__ import annotations

import glob
import json
import os
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"


def q(p, expr):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--expression", expr],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value")
    except Exception:
        return None


rows = []
for path in sorted(glob.glob(f"{CWD}/.waffle/documents/knowledge/*{EXT}")):
    rel = path[len(CWD) + 1:]
    name = os.path.basename(rel)[:-5]
    rows.append((
        name,
        q(rel, "status"),
        q(rel, "skillRefs") or [],
        q(rel, "agentRefs") or [],
    ))

print(f"{'名前':52} {'状態':10} skillRefs / agentRefs")
for name, st, sk, ag in rows:
    print(f"{name[:52]:52} {str(st):10} {sk} / {ag}")

cand = [r for r in rows if r[0].startswith("knowledge-cand")]
book = [r for r in rows if not r[0].startswith("knowledge-cand")]
print(f"\n候補 {len(cand)} 件 / それ以外 {len(book)} 件")
print("候補のうち skillRefs を持つもの:",
      [r[0] for r in cand if r[2]])

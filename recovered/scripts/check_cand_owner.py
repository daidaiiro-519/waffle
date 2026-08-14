"""knowledge候補が誰のものとして宣言されているかを、find_all で正しく読む。"""
from __future__ import annotations

import glob
import json
import os
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"


def field(rel, name):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "find_all",
                        "--path", rel, "--fieldName", name],
                       capture_output=True, text=True, cwd=CWD)
    try:
        v = json.loads(r.stdout).get("value") or []
        return v[0] if v else None
    except Exception:
        return None


rows = []
for path in sorted(glob.glob(f"{CWD}/.waffle/documents/knowledge/knowledge-cand-*{EXT}")):
    rel = path[len(CWD) + 1:]
    rows.append((os.path.basename(rel)[:-5],
                 field(rel, "status"),
                 field(rel, "skillRefs"),
                 field(rel, "agentRefs")))

print(f"{'候補':52} {'状態':10} skillRefs / agentRefs")
for n, st, sk, ag in rows:
    mark = "  ← advisor 側" if sk else ""
    print(f"{n[:52]:52} {str(st):10} {sk} / {ag}{mark}")

odd = [n for n, _, sk, _ in rows if sk]
print(f"\n候補 {len(rows)} 件中、skillRefs を持つもの {len(odd)} 件: {odd}")

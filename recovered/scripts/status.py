"""bc-waffle の仕様が、いまどの版でどんな状態かを数える。"""
from __future__ import annotations

import glob
import json
import subprocess
from collections import Counter

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"

ver = Counter()
state = Counter()
todo = []
for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/bc-waffle/**/*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    name = rel.split("/")[-1][:-5]
    r = subprocess.run(["uv", "run", "waffle", "validate", "--path", rel],
                       capture_output=True, text=True, cwd=CWD)
    out = (r.stdout or r.stderr).strip()
    try:
        d = json.loads(out)
    except Exception:
        d = {}
    v = d.get("schemaRef", "?")
    ver[v] += 1
    if d.get("status"):
        state["適合"] += 1
    else:
        state["不適合"] += 1
        todo.append((name, v, (d.get("error") or out)[:70]))

print("版の分布:", dict(ver))
print("状態:", dict(state))
print(f"\n不適合 {len(todo)} 件（先頭10件）")
for n, v, e in todo[:10]:
    print(f"  {n:38} {v:22} {e}")

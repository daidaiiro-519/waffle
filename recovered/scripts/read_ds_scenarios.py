"""移設対象の業務サービスのシナリオを読む。"""
from __future__ import annotations

import json
import subprocess
import sys

CWD = "/home/daidaiiro/workspace/waffle"
B = ".waffle/documents/specs/bc-waffle/bc-waffle." + "json"


def q(block, expr):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", B, "--blockKey", block, "--expression", expr],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout)["value"]
    except Exception:
        return []


targets = sys.argv[1:]
svc = {s["name"]: s for s in q("domainServices", "items")}
for name in targets:
    s = svc.get(name)
    print(f"════ {name}  ({s['serviceName'] if s else '?'})")
    if s:
        print("  責務:", s["responsibility"][:220])
    print()
    for x in q("domainServiceScenarios", "scenarios"):
        if name not in (x.get("covers") or ""):
            continue
        print(f"  ■ {x['name']}  [{x.get('category')}]")
        print(f"    観点: {x.get('viewpoint','')[:100]}")
        for line in (x.get("gherkin") or "").splitlines():
            print("      " + line)
        print()

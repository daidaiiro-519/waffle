"""移設する業務サービスと、既存シナリオの割り当てを見る。"""
from __future__ import annotations

import json
import subprocess
from collections import Counter

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


svc = q("domainServices", "items")
sc = q("domainServiceScenarios", "scenarios[].{n:name,c:covers}")
cnt = Counter((x.get("c") or "（未記入）") for x in sc)

print(f"業務サービス {len(svc)} 件 / シナリオ {len(sc)} 件\n")
for s in svc:
    keys = [k for k in cnt if s["name"] in k]
    n = sum(cnt[k] for k in keys)
    print(f"  {s['name']:24} {s['serviceName']:30} 束={s.get('group',''):22} シナリオ {n}")

rest = [k for k in cnt if not any(s["name"] in k for s in svc)]
if rest:
    print("\n  どの業務サービスにも結び付かない covers:")
    for k in rest:
        print(f"    {k}  ({cnt[k]} 件)")

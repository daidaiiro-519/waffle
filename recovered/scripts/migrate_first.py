"""最初の1文書を v9 へ移す。符号を振り、シナリオが満たす基準を指すようにする。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = (".waffle/documents/specs/bc-waffle/subdomain/sd-reconciliation/"
     "usecase/uc-check-criteria-coverage.json")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(block, expr):
    return json.loads(run("query", "--operation", "query_path", "--path", P,
                          "--blockKey", block, "--expression", expr))["value"]


print("── 版を移す :", run("scaffold", "--operation", "migrate_schema", "--path", P,
                       "--schemaRef", "DomainSpecSchema/v9")[:160])

CRIT_IDS = ["reports-unreferenced", "reports-dangling", "reports-duplicate-ids",
            "reports-unlinked-scenarios", "reports-omission",
            "empty-when-complete", "scans-root"]
crit = q("acceptanceCriteria", "items")
assert len(crit) == len(CRIT_IDS), f"基準の数が合わない: {len(crit)}"
new_crit = [{"id": i, "text": t} for i, t in zip(CRIT_IDS, crit)]

guar = q("operationGuarantees", "items")
new_guar = [{"id": "invalid-path", "text": guar[0]}]

SATISFIES = [["reports-unreferenced"], ["reports-dangling"], ["reports-duplicate-ids"],
             ["reports-unlinked-scenarios"], ["reports-omission"],
             ["empty-when-complete"], ["scans-root"]]
scen = q("acceptanceScenarios", "scenarios")
assert len(scen) == len(SATISFIES), f"シナリオの数が合わない: {len(scen)}"
for s, ids in zip(scen, SATISFIES):
    s.pop("covers", None)
    s["satisfies"] = ids

gscen = q("guaranteeScenarios", "scenarios")
for s in gscen:
    s.pop("covers", None)
    s["satisfies"] = ["invalid-path"]

print("── 値を書き込む :", run("scaffold", "--operation", "fill", "--path", P, "--values",
                        json.dumps({"content.acceptanceCriteria.items": new_crit,
                                    "content.operationGuarantees.items": new_guar,
                                    "content.acceptanceScenarios.scenarios": scen,
                                    "content.guaranteeScenarios.scenarios": gscen},
                                   ensure_ascii=False))[:200])
print("── 検証 :", run("validate", "--path", P)[:220])

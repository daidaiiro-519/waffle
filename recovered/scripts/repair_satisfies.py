"""移設した筋書きの対応先を、保証の並び順に沿って付け直す。"""
from __future__ import annotations

import json
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SRC = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/guarantees_dump." + "json")
CODE = re.compile(r"[A-Z]{3,}(?:_[A-Z]+)+")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(p, b, e):
    try:
        return json.loads(run("query", "--operation", "query_path", "--path", p,
                              "--blockKey", b, "--expression", e))["value"]
    except Exception:
        return None


with open(SRC, encoding="utf-8") as f:
    dump = json.load(f)

for name, v in dump["usecases"].items():
    if v["bc"] != "bc-waffle":
        continue
    path = v["path"]
    moved_texts = [(g if isinstance(g, str) else g.get("text", "")) for g in v["guarantees"]
                   if not CODE.search(g if isinstance(g, str) else g.get("text", ""))]
    if not moved_texts:
        continue
    crit = q(path, "acceptanceCriteria", "items") or []
    if not crit or not isinstance(crit[0], dict):
        continue                      # v8 は covers 文字列のままなので触らない
    by_text = {c["text"]: c["id"] for c in crit}
    ids = [by_text[t] for t in moved_texts if t in by_text]
    if not ids:
        continue

    scen = q(path, "acceptanceScenarios", "scenarios") or []
    moved_names = set(v["guaranteeScenarios"])
    k = 0
    fixed = 0
    for s in scen:
        if s.get("name") in moved_names:
            s["satisfies"] = [ids[min(k, len(ids) - 1)]]
            k += 1
            fixed += 1
    if not fixed:
        continue
    run("scaffold", "--operation", "fill", "--path", path,
        "--values", json.dumps({"content.acceptanceScenarios.scenarios": scen},
                               ensure_ascii=False))
    ver = run("validate", "--path", path)
    print(f"  {name:38} 付け直し {fixed} 件  "
          f"{'OK' if '\"VALIDATED\"' in ver else ver[:110]}")

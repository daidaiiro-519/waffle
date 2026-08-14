"""DRAFT の knowledge 候補を、全ブロック読み出す。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
OUT = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/drafts_dump." + "json")

NAMES = [
    "knowledge-cand-aggregate-declaration-is-not-class-existence",
    "knowledge-cand-edge-delivery-browser-trust-boundary",
    "knowledge-cand-first-class-concept-vs-premature-generalization",
    "knowledge-cand-metaphor-must-still-say-the-thing",
    "knowledge-cand-usecase-does-not-restate-service",
]
BLOCKS = ["title", "description", "principles", "classifications",
          "decisionCriteria", "examples", "antiPatterns",
          "provenance", "relatedConcepts"]


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


data = {}
for n in NAMES:
    path = f".waffle/documents/knowledge/{n}." + "json"
    doc = {}
    for b in BLOCKS:
        out = run("query", "--operation", "query_path", "--path", path,
                  "--blockKey", b, "--expression", "@")
        try:
            doc[b] = json.loads(out)["value"]
        except Exception:
            doc[b] = None
    data[n] = doc

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

for n, doc in data.items():
    have = [b for b, v in doc.items() if v]
    print(f"{n[:56]:56} ブロック {len(have)}/9")
print("\n→", OUT)

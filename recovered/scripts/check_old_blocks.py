"""旧要約版の器（原則・分類・判断基準・実例・アンチパターン）が残っていないかを確かめる。"""
from __future__ import annotations

import json
import subprocess

DOCS = ["subdomain", "bounded-context", "domain-model", "business-logic-simple",
        "evolving-design", "ubiquitous-language", "design-heuristics",
        "architecture-patterns", "event-sourced-domain-model", "context-integration",
        "communication", "business-domain", "domain-expert", "event-storming",
        "real-world-ddd"]
OLD = ("principles", "classifications", "decisionCriteria", "examples", "antiPatterns")

for d in DOCS:
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", f".waffle/documents/knowledge/{d}." + "json",
                        "--expression", "@"],
                       capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
    keys = {b["blockKey"] for b in json.loads(r.stdout)["results"]}
    left = sorted(keys & set(OLD))
    print(f"{d:32} 旧ブロックの残り: {left or 'なし'}")
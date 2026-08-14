"""19本すべてが v6 で ACTIVE になり、旧ブロックが残っていないことを確かめる。"""
from __future__ import annotations

import json
import pathlib
import subprocess

A = ".waffle/skills/ddd-advisor/references/archive/knowledge-v1-book-transcription"
DOCS = ["business-domain", "domain-expert", "subdomain", "ubiquitous-language",
        "bounded-context", "context-integration", "business-logic-simple",
        "domain-model", "event-sourced-domain-model", "architecture-patterns",
        "communication", "design-heuristics", "evolving-design", "event-storming",
        "real-world-ddd", "microservices", "event-driven-architecture",
        "data-mesh", "closing-heuristics"]
OLD = {"principles", "classifications", "decisionCriteria", "examples", "antiPatterns"}

tot_new = tot_src = 0
bad = []
print(f"{'':30} {'書起し':>6} {'変換後':>6}  図 注釈")
for d in DOCS:
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", f".waffle/documents/knowledge/{d}." + "json",
                        "--expression", "@"], capture_output=True, text=True,
                       cwd="/home/daidaiiro/workspace/waffle")
    keys = {b["blockKey"] for b in json.loads(r.stdout)["results"]}
    if keys & OLD:
        bad.append((d, sorted(keys & OLD)))
    md = pathlib.Path(f".waffle/knowledge/ACTIVE/{d}.md").read_text(encoding="utf-8")
    src = len(pathlib.Path(f"{A}/{d}.md").read_text(encoding="utf-8").splitlines())
    new = len(md.splitlines())
    tot_new += new
    tot_src += src
    print(f"{d:30} {src:6} {new:6}  {md.count('```mermaid'):2} "
          f"{md.count('| どこの話か |'):2}")
print(f"{'合計':30} {tot_src:6} {tot_new:6}")
print("旧ブロックの残り:", bad or "なし")
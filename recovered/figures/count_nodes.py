"""19本のノード数・図・注釈・原文を数える。"""
from __future__ import annotations

import json
import pathlib
import subprocess

DOCS = ["business-domain","domain-expert","subdomain","ubiquitous-language",
        "bounded-context","context-integration","business-logic-simple","domain-model",
        "event-sourced-domain-model","architecture-patterns","communication",
        "design-heuristics","evolving-design","event-storming","real-world-ddd",
        "microservices","event-driven-architecture","data-mesh","closing-heuristics"]


def count(nodes):
    t = 0
    for n in nodes:
        t += 1 + count(n.get("children", []))
    return t


tot = figs = notes = verb = 0
for d in DOCS:
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", f".waffle/documents/knowledge/{d}." + "json",
                        "--blockKey", "nodes", "--expression", "items"],
                       capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
    items = json.loads(r.stdout)["value"]
    tot += count(items)
    md = pathlib.Path(f".waffle/knowledge/ACTIVE/{d}.md").read_text(encoding="utf-8")
    figs += md.count("```mermaid")
    notes += md.count("| どこの話か |")
    verb += md.count("```") // 2 - md.count("```mermaid")

print(f"ノード合計: {tot}  図: {figs}  注釈の表: {notes}  原文（コード塊）: {verb}")
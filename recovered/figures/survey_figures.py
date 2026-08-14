"""注釈がまだ空の図を洗い出し、書くのに要る材料（節点・辺・囲み）を並べる。"""
from __future__ import annotations

import json
import subprocess

DOCS = ["subdomain", "bounded-context", "domain-model", "business-logic-simple",
        "evolving-design", "ubiquitous-language"]


def walk(nodes, path=()):
    for n in nodes:
        here = path + (n["name"],)
        if "figure" in n:
            yield here, n["figure"]
        yield from walk(n.get("children", []), here)


for d in DOCS:
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", f".waffle/documents/knowledge/{d}." + "json",
                        "--blockKey", "nodes", "--expression", "items"],
                       capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
    items = json.loads(r.stdout)["value"]
    for path, fig in walk(items):
        print(f"\n=== {d} / {' > '.join(path)}")
        print(f"  意図: {fig.get('intent','')}")
        print(f"  読み取り: {fig.get('reading','')[:110]}")
        if fig.get("groups"):
            print(f"  囲み: {[(g.get('label'), g.get('nodes')) for g in fig['groups']]}")
        print(f"  節点: {fig.get('nodes')}")
        for e in fig.get("edges", []):
            print(f"    {e.get('from')} -> {e.get('to')}"
                  + (f"  「{e['label']}」" if e.get("label") else ""))
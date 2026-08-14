"""注釈を持たない図を洗い出す。"""
from __future__ import annotations

import json
import subprocess


def walk(nodes, path=()):
    for n in nodes:
        here = path + (n["name"],)
        if "figure" in n:
            yield here, n["figure"]
        yield from walk(n.get("children", []), here)


r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                    "--path", ".waffle/documents/knowledge/subdomain." + "json",
                    "--blockKey", "nodes", "--expression", "items"],
                   capture_output=True, text=True, cwd="/home/daidaiiro/workspace/waffle")
for path, fig in walk(json.loads(r.stdout)["value"]):
    if not fig.get("notes"):
        print("注釈なし:", " > ".join(path))
        print("  意図:", fig.get("intent"))
        print("  節点:", fig.get("nodes"))
        print("  囲み:", [(g.get("label"), g.get("nodes")) for g in fig.get("groups", [])])
        for e in fig.get("edges", []):
            print(f"    {e.get('from')} -> {e.get('to')}"
                  + (f"  「{e['label']}」" if e.get("label") else ""))
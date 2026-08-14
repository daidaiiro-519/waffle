"""NodesBlock の x-render を直す。

each は「繰り返す対象」ではなく「各要素へ適用する部品の並び」だった。
繰り返す対象は from。深さ3ぶんの入れ子を宣言する。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


LEAF = [{"as": "paragraph", "from": "summary"}]
CHILD = LEAF + [{"as": "section", "from": "children", "titleFrom": "name", "each": LEAF}]
ROOT = LEAF + [{"as": "section", "from": "children", "titleFrom": "name", "each": CHILD}]

XRENDER = [{"as": "section", "from": "items", "titleFrom": "name", "each": ROOT}]

print(run("patch-schema", "--operation", "set_field", "--schemaRef", "KnowledgeSchema/v6",
          "--params", json.dumps({"defName": None, "fieldPath": "$defs.NodesBlock.x-render",
                                  "value": XRENDER}, ensure_ascii=False))[:130])
print(run("render", "--path", ".waffle/documents/knowledge/subdomain." + "json")[:130])

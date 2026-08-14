"""KnowledgeSchema v6 の x-render を、拡張した語彙で書き直す。

ノードは 文章 → 図（意図・読み取り・図・関係の表）→ 原文（意図・読み取り・原文）→ 子 の順。
図は描画できない読み手のために、意図と読み取りを必ず先に出す。
"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


FIGURE_PARTS = [
    {"as": "paragraph", "from": "intent"},
    {"as": "paragraph", "from": "reading"},
    {"as": "graph", "from": "edges", "nodesFrom": "nodes", "groupsFrom": "groups"},
    {"as": "table", "from": "edges", "columns": [
        {"field": "from", "header": "から"},
        {"field": "to", "header": "へ"},
        {"field": "label", "header": "関係"},
    ]},
]

VERBATIM_PARTS = [
    {"as": "paragraph", "from": "intent"},
    {"as": "paragraph", "from": "reading"},
    {"as": "code", "from": "source", "langFrom": "lang"},
]

BODY = [
    {"as": "paragraph", "from": "summary"},
    {"as": "object", "from": "figure", "each": FIGURE_PARTS},
    {"as": "object", "from": "verbatim", "each": VERBATIM_PARTS},
]

LEAF = BODY
CHILD = BODY + [{"as": "section", "from": "children", "titleFrom": "name", "each": LEAF}]
ROOT = BODY + [{"as": "section", "from": "children", "titleFrom": "name", "each": CHILD}]

XRENDER = [{"as": "section", "from": "items", "titleFrom": "name", "each": ROOT}]

print(run("patch-schema", "--operation", "set_field", "--schemaRef", "KnowledgeSchema/v6",
          "--params", json.dumps({"defName": None, "fieldPath": "$defs.NodesBlock.x-render",
                                  "value": XRENDER}, ensure_ascii=False))[:120])
print(run("render", "--path", ".waffle/documents/knowledge/subdomain." + "json")[:120])

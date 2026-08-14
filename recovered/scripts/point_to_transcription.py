"""ddd-advisor が読む先を、要約版から書き起こし版へ向け直す。

要約版は器（KnowledgeSchema のブロック）に入るものだけを掬っており、
手順と関係の説明が19本すべてで落ちていた。判断の根拠として使えないため、
書き起こし版を読ませる。knowledge候補（knowledge-cand-*）は書き起こしに
対応物が無いので、要約版のまま残す。
"""
from __future__ import annotations

import json
import os
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
P = ".waffle/documents/skills/ddd-advisor." + "json"
ARCHIVE_REL = "references/archive/knowledge-v1-book-transcription"
ARCHIVE_ABS = f"{CWD}/.waffle/skills/ddd-advisor/{ARCHIVE_REL}"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


items = json.loads(run("query", "--operation", "query_path", "--path", P,
                       "--blockKey", "knowledgeRefs", "--expression", "items"))["value"]

moved, kept = [], []
for it in items:
    name = os.path.basename(it["path"])
    if os.path.exists(f"{ARCHIVE_ABS}/{name}"):
        it = {**it, "path": f"{ARCHIVE_REL}/{name}"}
        moved.append(name)
    else:
        kept.append(name)
    (moved if it["path"].startswith(ARCHIVE_REL) else kept) and None

new_items = []
for it in items:
    name = os.path.basename(it["path"])
    if os.path.exists(f"{ARCHIVE_ABS}/{name}"):
        new_items.append({**it, "path": f"{ARCHIVE_REL}/{name}"})
    else:
        new_items.append(it)

print(f"書き起こし版へ向けた: {len(moved)} 本")
print(f"要約版のまま残した: {len(kept)} 本 → {kept}")

print(run("scaffold", "--operation", "fill", "--path", P,
          "--values", json.dumps({"content.knowledgeRefs.items": new_items},
                                 ensure_ascii=False))[:180])
print(run("validate", "--path", P)[:200])

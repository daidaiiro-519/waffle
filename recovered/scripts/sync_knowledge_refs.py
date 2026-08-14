"""advisor の knowledgeRefs を、skillRefs が実際に配置しているものと突き合わせて揃える。

配置（skillRefs 由来）と宣言（knowledgeRefs）が二重管理になっており、
候補 knowledge が配置だけされて宣言に載っていない。宣言を実物へ追いつかせる。
"""
from __future__ import annotations

import glob
import json
import os
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"
ADVISORS = ["ddd-advisor", "tech-lead-advisor"]


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def field(rel, name):
    try:
        v = json.loads(run("query", "--operation", "find_all", "--path", rel,
                           "--fieldName", name))["value"]
        return v[0] if v else None
    except Exception:
        return None


# どの knowledge がどの advisor へ配られるかを、skillRefs から集める
targets = {a: [] for a in ADVISORS}
for path in sorted(glob.glob(f"{CWD}/.waffle/documents/knowledge/*{EXT}")):
    rel = path[len(CWD) + 1:]
    name = os.path.basename(rel)[:-5]
    if field(rel, "status") != "ACTIVE":
        continue
    for a in (field(rel, "skillRefs") or []):
        if a in targets:
            targets[a].append(name)

for advisor, names in targets.items():
    p = f".waffle/documents/skills/{advisor}." + EXT.lstrip(".")
    p = f".waffle/documents/skills/{advisor}." + "json"
    items = json.loads(run("query", "--operation", "query_path", "--path", p,
                           "--blockKey", "knowledgeRefs", "--expression", "items"))["value"]
    declared = {os.path.basename(it["path"]) for it in items}
    added = []
    for n in names:
        fn = f"{n}.md"
        if fn in declared:
            continue
        items.append({"path": f"references/knowledge/{fn}",
                      "description": "採用済みの knowledge 候補"})
        added.append(n)
    if not added:
        print(f"  [{advisor}] 追加なし（宣言済み {len(declared)}）")
        continue
    run("scaffold", "--operation", "fill", "--path", p,
        "--values", json.dumps({"content.knowledgeRefs.items": items}, ensure_ascii=False))
    v = run("validate", "--path", p)
    ok = '"ACTIVE"' in v or '"VALIDATED"' in v
    print(f"  [{advisor}] {len(added)} 件を宣言へ追加 {added} {'' if ok else v[:160]}")
    if ok:
        run("render", "--path", p)

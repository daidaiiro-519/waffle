"""審査の結果を反映する。

採用: aggregate-declaration-is-not-class-existence（Hookで実際に動いている検査に効く）
取り下げ: edge-delivery（仕様の話であって knowledge ではない）
削除: usecase-does-not-restate-service（既存 knowledge の言い直し）
移し済み: first-class-concept（evidence-based-scope へ吸収）
保留: metaphor（DRAFT のまま）
"""
from __future__ import annotations

import json
import os
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
K = ".waffle/documents/knowledge"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def fill(name, vals, label):
    path = f"{K}/{name}." + "json"
    run("scaffold", "--operation", "fill", "--path", path,
        "--values", json.dumps(vals, ensure_ascii=False))
    v = run("validate", "--path", path)
    ok = '"VALIDATED"' in v or '"ACTIVE"' in v or '"DEPRECATED"' in v
    print(f"  [{label}] {'反映' if ok else v[:200]}")
    if ok:
        run("render", "--path", path)


# 採用
fill("knowledge-cand-aggregate-declaration-is-not-class-existence", {
    "status": "ACTIVE",
    "agentRefs": ["waffle"],
}, "採用: 集約の宣言とクラスの存在は別のこと")

# 取り下げ（内容は残す）
fill("knowledge-cand-edge-delivery-browser-trust-boundary", {
    "status": "DEPRECATED",
    "content.provenance.caveats":
        "2026-08-11の審査で取り下げ。内容は特定の配信構成に固有の設計判断であり、"
        "横断して効く knowledge ではなく、その構成の仕様として書かれるべきものと判断した。"
        "記録としては残す。",
}, "取り下げ: 配信の端の信頼境界")

# 削除（今日作ったもの。既存 knowledge の言い直しだった）
for suffix in ("json",):
    p = f"{CWD}/{K}/knowledge-cand-usecase-does-not-restate-service.{suffix}"
    if os.path.exists(p):
        os.remove(p)
        print("  [削除] documents/knowledge/knowledge-cand-usecase-does-not-restate-service.json")

for p in (f"{CWD}/.waffle/knowledge/DRAFT/knowledge-cand-usecase-does-not-restate-service.md",
          f"{CWD}/.waffle/skills/ddd-advisor/references/knowledge/"
          f"knowledge-cand-usecase-does-not-restate-service.md",
          f"{CWD}/.claude/skills/ddd-advisor/references/knowledge/"
          f"knowledge-cand-usecase-does-not-restate-service.md"):
    if os.path.exists(p) or os.path.islink(p):
        os.remove(p)
        print("  [削除]", p[len(CWD) + 1:])

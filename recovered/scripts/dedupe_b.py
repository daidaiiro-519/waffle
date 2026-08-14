"""受け入れ基準と重なる操作保証を落とす（規約が「どちらか一方が余分」と裁いている）。"""
from __future__ import annotations

import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
S = ".waffle/documents/specs/bc-waffle"
PATCH = f"{S}/subdomain/sd-schema-management/usecase/uc-patch-schema." + "json"
SCAF = f"{S}/subdomain/sd-document-management/usecase/uc-scaffold-document." + "json"


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(path, block, expr="@"):
    return json.loads(run("query", "--operation", "query_path", "--path", path,
                          "--blockKey", block, "--expression", expr))["value"]


def apply(path, vals, label):
    run("scaffold", "--operation", "fill", "--path", path,
        "--values", json.dumps(vals, ensure_ascii=False))
    v = run("validate", "--path", path)
    ok = '"VALIDATED"' in v
    print(f"  [{label}] {'検証を通過' if ok else v[:220]}")
    if ok:
        run("render", "--path", path)


for path, label in ((PATCH, "uc-patch-schema"), (SCAF, "uc-scaffold-document")):
    g = q(path, "operationGuarantees", "items")
    gs = q(path, "guaranteeScenarios", "scenarios")

    # 冪等を述べる保証は、対応する受け入れ基準が「無変更で成功する」ことまで主張しており、
    # 保証側は同じ失敗を返し続ける場合も「べき等」に含んでしまうため、主張が少ない側を落とす。
    drop_ids = {x["id"] for x in g if "べき等" in x["text"]}
    kept_g = [x for x in g if x["id"] not in drop_ids]
    kept_gs = [s for s in gs if "べき等" not in s["name"]]

    print(f"  [{label}] 落とす保証 {len(drop_ids)}件 / 落とす筋書き {len(gs) - len(kept_gs)}件")
    apply(path, {"content.operationGuarantees.items": kept_g,
                 "content.guaranteeScenarios.scenarios": kept_gs}, label)
    print(f"     操作保証 {len(g)}→{len(kept_g)} / 保証シナリオ {len(gs)}→{len(kept_gs)}")

"""bc-waffle の残りの操作保証を、受け入れ基準と受け入れシナリオへ移す。

いずれも筋書きで確かめられる個別命題であり、状態の持ち主を持たない
業務ユースケースに全称の置き場所は無い、という再定義に従う。
"""
from __future__ import annotations

import json
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SRC = ("/tmp/claude-1000/-home-daidaiiro-workspace-waffle/"
       "72eb43b2-7db1-4b99-ac18-e3a9f9b91fbd/scratchpad/guarantees_dump." + "json")
CODE = re.compile(r"[A-Z]{3,}(?:_[A-Z]+)+")


def run(*a):
    r = subprocess.run(["uv", "run", "waffle", *a], capture_output=True, text=True, cwd=CWD)
    return (r.stdout or r.stderr).strip()


def q(p, b, e):
    try:
        return json.loads(run("query", "--operation", "query_path", "--path", p,
                              "--blockKey", b, "--expression", e))["value"]
    except Exception:
        return None


def slug(text: str, used: set) -> str:
    """主張の要点から、重ならない識別子を作る。"""
    base = "guarantee"
    for k, s in (("べき等", "idempotent"), ("冪等", "idempotent"), ("同じ結果", "same-result"),
                 ("同一の判定", "same-verdict"), ("同一の成果物", "deterministic-output"),
                 ("一切変えない", "read-only"), ("書き換えない", "read-only"),
                 ("最小diff", "minimal-diff"), ("保持", "preserves"), ("省略", "omits"),
                 ("描画しない", "not-rendered"), ("区切り線", "no-divider"),
                 ("実行しない", "does-not-execute"), ("組み立てる", "derives-name"),
                 ("missing_placement", "missing-placement"),
                 ("Document 全体", "targets-document")):
        if k in text:
            base = s
            break
    i, out = 1, base
    while out in used:
        i += 1
        out = f"{base}-{i}"
    return out


with open(SRC, encoding="utf-8") as f:
    dump = json.load(f)

for name, v in dump["usecases"].items():
    if v["bc"] != "bc-waffle":
        continue
    path = v["path"]
    rest = [g for g in v["guarantees"]
            if not CODE.search(g if isinstance(g, str) else g.get("text", ""))]
    if not rest:
        continue

    crit = q(path, "acceptanceCriteria", "items") or []
    is_v9 = bool(crit) and isinstance(crit[0], dict)
    used = {c["id"] for c in crit} if is_v9 else set()
    have_text = {(c if isinstance(c, str) else c["text"]) for c in crit}

    scen = q(path, "acceptanceScenarios", "scenarios") or []
    gs = q(path, "guaranteeScenarios", "scenarios") or []

    added = skipped = 0
    for g in rest:
        t = g if isinstance(g, str) else g.get("text", "")
        if t in have_text:          # 既に基準にある主張は捨てる
            skipped += 1
            continue
        i = (g.get("id") if isinstance(g, dict) else None) or slug(t, used)
        while i in used:
            i = slug(t, used | {i})
        used.add(i)
        crit.append({"id": i, "text": t} if is_v9 else t)
        added += 1

    # 保証シナリオを受け入れシナリオへ移す（対応先は最後に足した基準へ寄せる）
    for s in gs:
        s = dict(s)
        s.pop("covers", None)
        if is_v9:
            s["satisfies"] = [sorted(used)[0]] if not crit else [crit[-1]["id"]]
        else:
            s["covers"] = "操作保証からの移設"
        scen.append(s)

    vals = {"content.acceptanceCriteria.items": crit,
            "content.acceptanceScenarios.scenarios": scen,
            "content.operationGuarantees.items": [],
            "content.guaranteeScenarios.scenarios": []}
    run("scaffold", "--operation", "fill", "--path", path,
        "--values", json.dumps(vals, ensure_ascii=False))
    print(f"  {name:38} 基準へ {added} 件 / 既出につき捨てた {skipped} 件 / 筋書き {len(gs)} 件")

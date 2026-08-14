"""集約の不変条件が、ユースケース側の宣言に対応を持っているかを見る。

ユースケースの受け入れ基準・操作保証を全部集めて、語の重なりで当たりを付ける。
判定は人がするので、候補を出すところまで。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
S = pathlib.Path(CWD) / ".waffle/documents/specs/bc-artifact-share"


def q(path, block, expr):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value") or []
    except Exception:
        return []


# ユースケース側の宣言をすべて集める
declared = []
for p in sorted((S / "subdomain/sd-artifact-sharing/usecase").glob("uc-*.json")):
    rel = str(p.relative_to(CWD))
    for x in q(rel, "acceptanceCriteria", "items"):
        declared.append((p.stem, "受入", x))
    for x in q(rel, "operationGuarantees", "items"):
        declared.append((p.stem, "保証", x))

print(f"ユースケース側の宣言: {len(declared)} 件\n")


def words(t):
    return set(re.findall(r"[ぁ-んァ-ヶ一-龠]{2,}", t))


for agg in ("agg-comment", "agg-shared-artifact", "agg-project"):
    rel = str((S / "aggregate" / f"{agg}.json").relative_to(CWD))
    print(f"■ {agg}")
    for inv in q(rel, "invariants", "items[].rule"):
        w = words(inv)
        best = sorted(declared, key=lambda d: -len(w & words(d[2])))[:1]
        score = len(w & words(best[0][2])) if best else 0
        mark = "  " if score >= 4 else "??"
        print(f"  {mark} {inv[:44]}")
        if score >= 2:
            print(f"       ↔ [{best[0][0]}/{best[0][1]}] {best[0][2][:52]} (重なり{score})")
        else:
            print("       ↔ 対応が見当たらない")
    print()

"""受け入れ基準と操作保証の両方に冪等を書いている仕様が残っていないか走査する。"""
from __future__ import annotations

import glob
import json
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"


def q(p, b, e):
    r = subprocess.run(["uv", "run", "waffle", "query", "--operation", "query_path",
                        "--path", p, "--blockKey", b, "--expression", e],
                       capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value")
    except Exception:
        return None


def texts(items):
    return [(x if isinstance(x, str) else x.get("text", "")) for x in (items or [])]


hits = []
for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/usecase/uc-*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    nc = sum("べき等" in t for t in texts(q(rel, "acceptanceCriteria", "items")))
    ng = sum("べき等" in t for t in texts(q(rel, "operationGuarantees", "items")))
    if nc and ng:
        hits.append((rel.split("/")[-1][:-5], nc, ng))

if hits:
    for n, a, b in hits:
        print(f"  {n:44} 基準={a} 保証={b}")
else:
    print("  両方に冪等を書いている仕様は残っていません")

"""全ユースケースの操作保証を並べ、受け入れ基準・エラーで言えないかを見る。"""
from __future__ import annotations

import glob
import json
import subprocess
from collections import Counter

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


total = Counter()
rows = []
for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/usecase/uc-*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    name = rel.split("/")[-1][:-5]
    g = texts(q(rel, "operationGuarantees", "items"))
    if not g:
        continue
    c = texts(q(rel, "acceptanceCriteria", "items"))
    codes = q(rel, "errors", "items[].code") or []
    for t in g:
        total["保証の総数"] += 1
        rows.append((name, t, c, codes))

print(f"操作保証の総数: {total['保証の総数']}  （ユースケース {len({r[0] for r in rows})} 件）\n")

# 分類：エラー名を含むか／同じ趣旨の基準が既にあるか
KEY = ["べき等", "最小diff", "一切変更しない", "保持", "破壊されない"]
for name, t, c, codes in rows:
    mark = []
    hit = [x for x in codes if x in t]
    if hit:
        mark.append(f"errorsに同名 {hit}")
    # 基準側に同じ語幹があるか（粗い当たりを付けるだけ）
    for k in KEY:
        if k in t and any(k in cc for cc in c):
            mark.append(f"基準にも「{k}」")
    print(f"[{name}]")
    print(f"  {t[:110]}")
    print(f"  → {' / '.join(mark) if mark else '(重なり見当たらず)'}\n")

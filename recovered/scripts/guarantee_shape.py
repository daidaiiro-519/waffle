"""操作保証がどんな主張の形をしているか、筋書きを持っているかを数える。"""
from __future__ import annotations

import glob
import json
import re
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


ABSENCE = re.compile(r"残さない|残らない|失われない|取り出せない|一度しか|作り出さない|漏れ")
UNIVERSAL = re.compile(r"変わらない|変えない|書き換えられない|一切変更しない|保たれる|そのまま残る|べき等|破壊されない|二重に")
ERRORLIKE = re.compile(r"エラーを返す shall|_[A-Z]{2,}")

kind = Counter()
ng = tot = 0
for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/usecase/uc-*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    g = texts(q(rel, "operationGuarantees", "items"))
    if not g:
        continue
    s = q(rel, "guaranteeScenarios", "scenarios") or []
    tot += len(g)
    ng += len(s)
    for t in g:
        if ERRORLIKE.search(t):
            kind["個別のエラー契約（errorsと重なる）"] += 1
        elif ABSENCE.search(t):
            kind["情報の不在の主張"] += 1
        elif UNIVERSAL.search(t):
            kind["全称的な不変（どの操作のあとでも〜）"] += 1
        else:
            kind["その他"] += 1

print(f"操作保証 {tot} 件 / 保証シナリオ {ng} 件（{ng / tot:.0%} しか筋書きを持たない）\n")
for k, v in kind.most_common():
    print(f"  {k:34} {v:3} 件  ({v / tot:.0%})")

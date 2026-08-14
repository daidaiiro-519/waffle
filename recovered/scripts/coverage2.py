"""受け入れ基準のうち、対応する筋書きを持たないものを数え直す。

covers は「受け入れ基準: 」という前置き付きの言い換えで書かれることがあり、
基準の全文とは一致しない。前置きを外し、EARS の枠（When/If/While ... shall）も
外してから、中身どうしを突き合わせる。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
SPECS = pathlib.Path(CWD) / ".waffle/documents/specs/bc-artifact-share"


def q(path: str, block: str, expr: str):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", path, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    try:
        return json.loads(r.stdout).get("value")
    except Exception:
        return None


def core(text: str) -> str:
    """突き合わせに使える芯だけを残す。"""
    t = re.sub(r"^(受け入れ基準|操作保証)[:：]\s*", "", text.strip())
    t = re.sub(r"\s*shall\s*$", "", t)
    t = re.sub(r"^(When|If|While|Where)\s+.*?(?:とき|ならば|間)、\s*", "", t)
    t = re.sub(r"^[^、]{2,20}は\s+", "", t)
    return re.sub(r"[、。\s]", "", t)


def covered(criterion: str, covers: list[str]) -> bool:
    c = core(criterion)
    for cv in covers:
        v = core(cv)
        if not v:
            continue
        if v in c or c in v:
            return True
        # 語の重なりで見る（言い換えの度合いが大きい場合）
        if len(v) >= 8 and (v[:8] in c or c[:8] in v):
            return True
    return False


total = missing_total = 0
report = []
for p in sorted(SPECS.rglob("uc-*.json")):
    rel = str(p.relative_to(CWD))
    criteria = q(rel, "acceptanceCriteria", "items") or []
    scenarios = q(rel, "acceptanceScenarios", "scenarios") or []
    covers = [s.get("covers", "") for s in scenarios]
    missing = [c for c in criteria if not covered(c, covers)]
    total += len(criteria)
    missing_total += len(missing)
    if missing:
        report.append((p.stem, len(criteria), len(scenarios), missing))

print(f"受け入れ基準 {total} 件のうち、筋書きが見当たらないもの {missing_total} 件\n")
for name, n, s, missing in report:
    print(f"■ {name}（基準{n} / 筋書き{s}）")
    for m in missing:
        print(f"    - {m}")

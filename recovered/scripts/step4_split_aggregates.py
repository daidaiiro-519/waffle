"""値の棚から引いている集約クラス・集約の定数を、集約の棚へ移す。

旧モジュールでは同居していたので、棚を移す置換だけでは全部が値の側へ寄る。
集約に属するものだけをここで抜き出す。
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path("/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share")
DOMAIN = ROOT / "lambda" / "admin_api" / "domain"

# 集約の棚へ移す名前
TO_ENTITY = {
    "domain.value_objects.shared_artifact": (
        "domain.entities.shared_artifact",
        {"SharedArtifact", "MAX_PROJECTS", "MAX_TTL", "MAX_CONTENT_BYTES"},
    ),
    "domain.value_objects.project": ("domain.entities.project", {"Project"}),
}

IMPORT = re.compile(
    r"^from (domain\.value_objects\.(?:shared_artifact|project)) import "
    r"(\(.*?\)|[^\n(]*)(?=\n)",
    re.MULTILINE | re.DOTALL)


def bare(name: str) -> str:
    return name.split(" as ")[0].split("#")[0].strip()


changed = 0
for path in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in path.parts or path.is_relative_to(DOMAIN):
        continue
    text = original = path.read_text(encoding="utf-8")
    out = []
    last = 0
    for m in IMPORT.finditer(text):
        module, blob = m.group(1), m.group(2)
        dest, agg_names = TO_ENTITY[module]
        inner = blob.strip()
        parenthesised = inner.startswith("(")
        if parenthesised:
            inner = inner[1:-1]
        names = [n.strip() for n in inner.split(",") if n.strip()]
        stay = [n for n in names if bare(n) not in agg_names]
        move = [n for n in names if bare(n) in agg_names]
        if not move:
            continue
        lines = []
        if stay:
            lines.append(_render(module, stay))
        lines.append(_render(dest, move))
        out.append(text[last:m.start()])
        out.append("\n".join(lines))
        last = m.end()
    if out:
        out.append(text[last:])
        text = "".join(out)
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print("集約を分けた:", path.relative_to(ROOT))

print("合計", changed, "ファイル")

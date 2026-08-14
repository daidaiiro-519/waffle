"""取り込み先を、新しい棚へ書き換える。振る舞いは変えない。"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path("/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share")

# どの語がどの棚へ移ったか。1つの旧モジュールが2つの棚に分かれるものがあるので、
# モジュール名の置換ではなく、語ごとに行き先を決める
DEST = {
    # 集約（entities）
    "SharedArtifact": "domain.entities.shared_artifact",
    "MAX_TTL": "domain.entities.shared_artifact",
    "MAX_PROJECTS": "domain.entities.shared_artifact",
    "MAX_CONTENT_BYTES": "domain.entities.shared_artifact",
    "Project": "domain.entities.project",
    # 共有アーティファクトの値
    "ArtifactId": "domain.value_objects.shared_artifact",
    "PublisherId": "domain.value_objects.shared_artifact",
    "ArtifactStatus": "domain.value_objects.shared_artifact",
    "ArtifactDescriptor": "domain.value_objects.shared_artifact",
    "ReadFromContent": "domain.value_objects.shared_artifact",
    "EXTRACTED": "domain.value_objects.shared_artifact",
    "MANUAL": "domain.value_objects.shared_artifact",
    # プロジェクトの値
    "ProjectId": "domain.value_objects.project",
    "ProjectKey": "domain.value_objects.project",
    "ProjectOwner": "domain.value_objects.project",
    "ProjectScope": "domain.value_objects.project",
    "ProjectStatus": "domain.value_objects.project",
    "PERSONAL": "domain.value_objects.project",
    "SHARED": "domain.value_objects.project",
    "is_known_scope": "domain.value_objects.project",
    # 中身の指紋
    "ContentFingerprint": "domain.value_objects.artifact_content",
}

# 旧モジュール名 → 新モジュール名。語が分岐しないものはこちらで足りる
MODULE = {
    "domain.view_token": "domain.value_objects.view_token",
    "domain.view_subject": "domain.value_objects.view_subject",
    "domain.html_inspection": "domain.services.html_inspection",
    "domain.caller": "application.caller",
    "domain.identifier": "domain.value_objects.identifier",
}

# PUBLISHED / SUSPENDED は両方の棚にあり、同じ綴りで別の値ではない。
# どちらから引くかは、そのファイルが扱っている集約で決まる
AMBIGUOUS = {"PUBLISHED", "SUSPENDED"}

FROM_IMPORT = re.compile(
    r"^from (domain\.\w+(?:\.\w+)*) import \(([^)]*)\)$|^from (domain\.\w+(?:\.\w+)*) import (.+)$",
    re.MULTILINE)


def split_names(blob: str) -> list[str]:
    return [n.strip() for n in blob.replace("\n", " ").split(",") if n.strip()]


def rewrite(text: str, prefer: str) -> str:
    """取り込み文を書き換える。prefer は PUBLISHED/SUSPENDED の引き先。"""
    out: dict[str, set[str]] = {}
    spans: list[tuple[int, int]] = []

    for m in FROM_IMPORT.finditer(text):
        module = m.group(1) or m.group(3)
        names = split_names(m.group(2) or m.group(4) or "")
        if module in ("domain.shared_artifact", "domain.project", "domain.view_token",
                      "domain.view_subject", "domain.html_inspection", "domain.caller",
                      "domain.identifier"):
            spans.append(m.span())
            for name in names:
                bare = name.split(" as ")[0].split("#")[0].strip()
                if bare in AMBIGUOUS:
                    dest = prefer
                elif bare in DEST:
                    dest = DEST[bare]
                else:
                    dest = MODULE.get(module, module)
                out.setdefault(dest, set()).add(name)

    if not spans:
        return text

    lines = []
    for module in sorted(out):
        names = ", ".join(sorted(out[module]))
        line = f"from {module} import {names}"
        if len(line) > 96:
            line = f"from {module} import (\n    " + ",\n    ".join(sorted(out[module])) + ",\n)"
        lines.append(line)
    block = "\n".join(lines)

    # 最初の対象を置き換え、残りは消す
    result, last = [], 0
    for i, (s, e) in enumerate(spans):
        result.append(text[last:s])
        if i == 0:
            result.append(block)
        last = e
        if i > 0 and text[e:e + 1] == "\n":
            last = e + 1
    result.append(text[last:])
    return "".join(result)


def prefer_for(path: pathlib.Path, text: str) -> str:
    """PUBLISHED / SUSPENDED をどちらの棚から引くか、扱っている対象で決める。"""
    if "project" in path.name and "artifact" not in path.name:
        return "domain.value_objects.project"
    art = len(re.findall(r"ArtifactStatus|SharedArtifact", text))
    prj = len(re.findall(r"ProjectStatus|\bProject\b", text))
    return "domain.value_objects.project" if prj > art else "domain.value_objects.shared_artifact"


changed = 0
for path in sorted(ROOT.rglob("*.py")):
    if "__pycache__" in path.parts:
        continue
    if path.is_relative_to(ROOT / "lambda" / "admin_api" / "domain"):
        continue  # 棚の中は手で書き直し済み
    text = path.read_text(encoding="utf-8")
    if "domain." not in text:
        continue
    new = rewrite(text, prefer_for(path, text))
    # モジュール参照（import domain.x / domain.x.y(...)）も追随させる
    for old, dest in MODULE.items():
        new = new.replace(f"import {old}\n", f"import {dest}\n")
        new = re.sub(rf"\b{re.escape(old)}\.", dest + ".", new)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed += 1
        print("書き換え:", path.relative_to(ROOT))

print("合計", changed, "ファイル")

#!/usr/bin/env python3
"""引き継ぎ工程を飛ばした実装着手の通知（PostToolUse）。

CLAUDE.mdのフルサイクルは「調べる→決める→引き継ぐ→作る」。
specを書き終えた直後は成果物が積み上がって手が動く状態になり、
Handoffの存在を確認しないままコードへ進みやすい（2026-07-31に実際に発生）。

Skillパッケージ配下の実装ファイルが書かれたとき、そのSkillに対応する
Handoff documentが無ければ通知する。ブロックはしない——Handoffが不要な
軽微な修正も実在するため、判断の余地を残す。

Handoffの「中身が十分か」は判定しない。AI自身が証跡を書けてしまう以上、
どんな指標を採用しても自己申告の域を出ないため（enforce-spec-firstが
PreToolUseのdenyから通知へ格下げされたのと同じ理由）。
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

# .waffle/skills/<スキル名>/<以下のパス>
_SKILL_FILE = re.compile(r"\.waffle/skills/([^/]+)/(.+)$")

# 実装ではない成果物（仕様・知識・説明）。これらの書き込みでは通知しない。
_NOT_IMPLEMENTATION = (
    "SKILL.md",
    "README.md",
)
_NOT_IMPLEMENTATION_DIRS = ("references/",)

# 実装とみなす拡張子。文書の書き込みで鳴らないよう絞る。
_IMPLEMENTATION_SUFFIXES = (
    ".py",
    ".js",
    ".mjs",
    ".ts",
    ".sh",
    ".yaml",
    ".yml",
    ".html",
)


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _is_implementation(rel_path: str) -> bool:
    """スキルパッケージ内の相対パスが実装ファイルかを判定する。"""
    if rel_path in _NOT_IMPLEMENTATION:
        return False
    if rel_path.startswith(_NOT_IMPLEMENTATION_DIRS):
        # references配下は仕様・知識・雛形の置き場で、原則として実装ではない。
        # 例外は配信の実体を成す雛形（閲覧画面・アップロード画面等）で、これは
        # templates直下に置く。templates/doc配下は共有される文書の雛形であり、
        # 配信の仕組みとは無関係なので対象外のままとする。
        rest = rel_path[len("references/templates/"):] if rel_path.startswith("references/templates/") else None
        if not (rest and "/" not in rest and rest.endswith(".html")):
            return False
    return rel_path.endswith(_IMPLEMENTATION_SUFFIXES)


def _entered_full_cycle(root: str, skill: str) -> bool:
    """そのSkillがフルサイクルに入っているか（ドメイン仕様を持つか）を判定する。

    仕様を持たないSkill（試作として作られたもの等）は引き継ぎ工程の対象外。
    仕様を書いたのに引き継ぎを飛ばした場合だけを検知したい。
    """
    return bool(glob.glob(os.path.join(root, f".waffle/documents/specs/bc-{skill}/**/*.json"), recursive=True))


def _handoff_exists(root: str, skill: str) -> bool:
    """そのSkillに言及するHandoff documentがあるかを探す。"""
    pattern = os.path.join(root, ".waffle/documents/handoff/*.json")
    for path in glob.glob(pattern):
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except OSError:
            continue
        if skill in raw:
            return True
    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    m = _SKILL_FILE.search(file_path.replace("\\", "/"))
    if not m:
        sys.exit(0)

    skill, rel_path = m.group(1), m.group(2)
    if not _is_implementation(rel_path):
        sys.exit(0)

    root = _project_root()
    if not _entered_full_cycle(root, skill):
        sys.exit(0)
    if _handoff_exists(root, skill):
        sys.exit(0)

    print(
        f"[Hook] {skill} の実装ファイル（{rel_path}）を書き込みましたが、"
        f"{skill} に対応する Handoff document が .waffle/documents/handoff/ に見つかりません。"
        "フルサイクルは「調べる→決める→引き継ぐ→作る」であり、"
        "specだけでは advisor から得た設計観点・実装観点が実装へ渡りません。"
        "引き継ぎ工程を飛ばしていないか確認してください"
        "（軽微な修正で引き継ぎが不要なら、この通知は無視して構いません）。",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

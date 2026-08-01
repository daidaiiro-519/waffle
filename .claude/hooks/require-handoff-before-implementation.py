#!/usr/bin/env python3
"""引き継ぎ工程を飛ばした実装着手を、書き込む前に知らせる（PreToolUse）。

CLAUDE.mdのフルサイクルは「調べる→決める→引き継ぐ→作る」。
specを書き終えた直後は成果物が積み上がって手が動く状態になり、
Handoffの存在を確認しないままコードへ進みやすい。

判定はユースケース単位で行う。Skill単位で「Handoffがあるか」を見ると、
最初のHandoffができた時点で以後どれだけ仕様を足しても通ってしまう
（2026-08-01に実際に発生。プロジェクトの仕様6件を足したあと、
既存のhandoff-artifact-shareがSkill名を含むために鳴らなかった）。

引き継ぎの「中身が十分か」は判定しない。AI自身が証跡を書けてしまう以上、
どんな指標を採用しても自己申告の域を出ないため。ここで見るのは、
仕様があるユースケースのうち、どのHandoffからも指されていないものの有無だけ。

ブロックはしない。引き継ぎが不要な軽微な修正も実在するため、判断の余地を残す。
書き込みの前に出すことで、手を動かし始める前に気づけるようにする。
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

# .waffle/skills/<スキル名>/<以下のパス>
_SKILL_FILE = re.compile(r"\.waffle/skills/([^/]+)/(.+)$")

# 実装ではない成果物（仕様・知識・説明）。これらの書き込みでは知らせない。
_NOT_IMPLEMENTATION = ("SKILL.md", "README.md")
_NOT_IMPLEMENTATION_DIRS = ("references/",)

# 実装とみなす拡張子。文書の書き込みで鳴らないよう絞る。
_IMPLEMENTATION_SUFFIXES = (".py", ".js", ".mjs", ".ts", ".sh", ".yaml", ".yml", ".html")


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
        rest = (rel_path[len("references/templates/"):]
                if rel_path.startswith("references/templates/") else None)
        if not (rest and "/" not in rest and rest.endswith(".html")):
            return False
    return rel_path.endswith(_IMPLEMENTATION_SUFFIXES)


def _usecase_ids(root: str, skill: str) -> list[str]:
    """そのSkillのドメイン仕様が持つユースケースの識別子を集める。"""
    pattern = os.path.join(root, f".waffle/documents/specs/bc-{skill}/**/usecase/*.json")
    ids = []
    for path in glob.glob(pattern, recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        # 置き換えられた仕様は、引き継ぎを求める対象から外す
        if doc.get("status") == "SUPERSEDED":
            continue
        if doc.get("documentId"):
            ids.append(doc["documentId"])
    return sorted(ids)


def _handed_over(root: str) -> str:
    """Handoff documentの中身をまとめて返す。どれが何を指しているかを探すため。"""
    chunks = []
    for path in glob.glob(os.path.join(root, ".waffle/documents/handoff/*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                chunks.append(f.read())
        except OSError:
            continue
    return "\n".join(chunks)


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
    usecases = _usecase_ids(root, skill)
    if not usecases:
        # 仕様を持たないSkillは引き継ぎ工程の対象外。
        # 仕様を書いたのに引き継ぎを飛ばした場合だけを知らせたい
        sys.exit(0)

    handoffs = _handed_over(root)
    missing = [uc for uc in usecases if uc not in handoffs]
    if not missing:
        sys.exit(0)

    listed = "、".join(missing[:6]) + ("ほか" if len(missing) > 6 else "")
    print(
        f"[Hook] {skill} の実装ファイル（{rel_path}）を書こうとしていますが、"
        f"どのHandoffからも指されていないユースケースが{len(missing)}件あります: {listed}。"
        "フルサイクルは「調べる→決める→引き継ぐ→作る」であり、specだけでは"
        "設計観点・実装観点が実装へ渡りません。着手する前に、引き継ぎ文書を"
        "作って提示したかを確認してください"
        "（この書き込みがそれらのユースケースと無関係なら、無視して構いません）。",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

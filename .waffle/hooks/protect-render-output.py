#!/usr/bin/env python3
"""論点4（Orchestratorスキーマ再設計ブレスト）: 投影（render出力）への直接
編集を防ぐ（PreToolUse）。

判定ロジックはuc-check-path-is-projection（CheckPathIsProjection）へ切り出し
済み。このスクリプトは、Edit/Writeツールの対象パスの実体（symlink解決済み
絶対パス）をリポジトリルート相対パスへ変換し、CLI経由でそのusecaseを呼び出す
だけの薄い駆動アダプターである。新しい判定ロジックはここに持ち込まない。

投影（document.jsonからのrender出力）への直接編集は、次のrenderで上書きされて
変更が消失する、あるいは原本と投影が食い違ったまま気づかれない、という事故を
引き起こす（実際に発生済み）。原本（document.json/schema.json）自体は
protect-document-json.py / protect-raw-json-access.pyが別途保護しており、
本hookはそれと対になる「投影側」の保護を担う。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _run_waffle(*args: str) -> dict | None:
    result = subprocess.run(
        ["uv", "run", "--project", ".", "waffle", *args],
        cwd=_project_root(), capture_output=True, text=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    root = _project_root()
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(root, file_path)
    resolved = os.path.realpath(abs_path)
    try:
        rel_path = os.path.relpath(resolved, root)
    except ValueError:
        sys.exit(0)  # 別ドライブ等、相対化できない場合は許可する（安全側）

    result = _run_waffle("check-path-is-projection", "--resolved-path", rel_path)
    if result is None or not result.get("isProjection"):
        sys.exit(0)

    kind = result.get("documentKind")
    doc_id = result.get("documentId")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{file_path} はdocument.json（{kind}: {doc_id}）からの投影（render出力）です。"
                "直接編集すると次のrenderで上書きされて変更が消失します。"
                "対象document.jsonをscaffold fillで更新してからrenderしてください。"
            ),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

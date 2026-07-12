#!/usr/bin/env python3
"""候補5: document.json直接編集の禁止（PreToolUse）。

CLAUDE.mdの運用ルール「document.json操作は必ずCLI/MCP経由で行う」を、
Edit/Writeツール呼び出しの時点で機械的に強制する。例外は無い
（唯一の近い例外はschemaファイル側の話であり、document.jsonには適用されない）。

docs/brainstorm/brainstorm-waffle-hooks.mdの候補5シミュレーションをそのまま
本番用に採用したもの。
"""
from __future__ import annotations

import json
import re
import sys

_TARGET = re.compile(r"\.waffle/documents/.*\.json$")


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")

    if _TARGET.search(file_path):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "document.json は CLI/MCP 経由（scaffold fill / clear_field / "
                    f"patch-schema）で編集してください。直接Edit/Writeで書き込もう"
                    f"としたパス: {file_path}"
                ),
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

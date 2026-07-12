#!/usr/bin/env python3
"""候補5拡張: document.json/schema.jsonの直接「読み」の禁止（PreToolUse）。

候補5（protect-document-json.py）はEdit/Writeでの直接「書き」しか見ておらず、
Bashでのcat/grep/python3(json.load)等による直接「読み」・schemaファイル
（src/waffle/domain/model/**/*.json）へのアクセスは素通りしていた
（2026-07-13、実際にAIがpython3/cat/grepでdocument.json・schemaを直接
読んでいたことをユーザーが指摘して発覚）。

このHookは同じ「AIは値だけ、構造は機械が守る」というHarness原則を、読み取り側
（Read/Bash）にも対象パスをdocument.json＋schemaファイルの両方に広げて適用する。
waffle CLI（query --operation index_scan/get_field/get_block 等）自体の呼び出しと、
git（diff/show/log等の履歴確認）は対象外とする——両方とも直接ファイル内容を
AIの文脈に生で流し込んでschemaの構造検証・prompt付与を経由する経路を迂回する
ものではないため。
"""
from __future__ import annotations

import json
import re
import sys

_TARGET = re.compile(r"(\.waffle/documents/|src/waffle/domain/model/)[^\s'\"]*\.json")
_READ_VERB = re.compile(r"\b(cat|head|tail|less|more|bat|python3?|node|jq|sed|awk|grep|perl|ruby|php|tac|nl|strings|xxd|od)\b")
# "waffle" は .waffle/ パス自体にも現れるため、CLIサブコマンド呼び出しの形
# （waffle query / waffle scaffold 等）でのみ「正規の経路」とみなす。
_WAFFLE_CLI = re.compile(
    r"(?:^|[\s;&|])waffle\s+(query|render|validate|scaffold|patch-schema|"
    r"check-[a-z-]+|scan-source-code|lint-docstring)\b"
)


def _deny(reason_target: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "document.json / schema.json は waffle CLI 経由（query の "
                "index_scan → get_field/get_block、書き込みは scaffold fill / "
                f"patch-schema）で読んでください。直接読み取ろうとした対象: {reason_target}"
            ),
        }
    }, ensure_ascii=False))


def _looks_like_raw_json_access(command: str) -> bool:
    if command.strip().startswith("git"):
        return False
    if _WAFFLE_CLI.search(command):
        return False
    if not _TARGET.search(command):
        return False
    return bool(_READ_VERB.search(command))


def main() -> None:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")

    if tool_name == "Read":
        file_path = payload.get("tool_input", {}).get("file_path", "")
        if _TARGET.search(file_path):
            _deny(file_path)
            sys.exit(0)
    elif tool_name == "Bash":
        command = payload.get("tool_input", {}).get("command", "")
        if _looks_like_raw_json_access(command):
            _deny(command)
            sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()

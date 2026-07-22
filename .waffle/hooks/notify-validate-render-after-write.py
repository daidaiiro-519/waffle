#!/usr/bin/env python3
"""process-reliability論点3の残り部分（PostToolUse通知）。

Bash経由のwaffle scaffold --operation fill / waffle patch-schemaが
document.json・schema.jsonを書き換えた後、対応するwaffle validate・
waffle renderが同一セッション内で実行されたかを確認する。

このHookはfill/patch自体の実行直後には発火しない（validate/renderは
まだ未来のコマンドで、その時点では必ず「未実行」判定になり無意味な
通知になるため）。代わりに、fill/patch対象と異なるpath/schemaRefへの
「次のBashコマンド」が実行されたタイミングで発火し、直前のfill/patch
対象に対してvalidate・renderの両方が間に挟まっていたかを確認する
（＝作業の切り替わり＝閉じ忘れを検知する好機）。

check-drift-on-write.pyの責務（drift再検知）とは混同しない。ここで
確認するのはコマンドの実行有無のみで、内容の正しさは判定しない。
"""
from __future__ import annotations

import json
import os
import re
import sys

_FILL_CMD = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b")
_PATCH_CMD = re.compile(r"waffle\s+patch-schema\b")
_VALIDATE_CMD = re.compile(r"waffle\s+validate\b")
_RENDER_CMD = re.compile(r"waffle\s+render(-handoff-template)?\b")
_PATH_ARG = re.compile(r"--path\s+(\S+)")
_SCHEMA_REF_ARG = re.compile(r"--schema(?:Ref|-ref)\s+(\S+)")

_WAFFLE_CMD = re.compile(r"\bwaffle\s+\S+")


def _target(command: str) -> str | None:
    m = _PATH_ARG.search(command)
    if m:
        return m.group(1).strip("'\"")
    m = _SCHEMA_REF_ARG.search(command)
    if m:
        return m.group(1).strip("'\"")
    return None


def _bash_commands(transcript_text: str) -> list[str]:
    commands = []
    for line in transcript_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message", {})
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_input = block.get("input", {})
            command = tool_input.get("command")
            if isinstance(command, str) and _WAFFLE_CMD.search(command):
                commands.append(command)
    return commands


def main() -> None:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    transcript_path = payload.get("transcript_path", "")

    if not _WAFFLE_CMD.search(command):
        sys.exit(0)
    if not transcript_path:
        sys.exit(0)

    try:
        with open(transcript_path, encoding="utf-8") as f:
            transcript_text = f.read()
    except OSError:
        sys.exit(0)

    history = _bash_commands(transcript_text)
    history.append(command)

    # 直近のfill/patch対象を、その後のコマンド列から見て閉じられたか判定する。
    # 「次に別のtargetへ向けたコマンドが来た」時点でのみ発火する。
    last_write_target: str | None = None
    validated = False
    rendered = False

    for cmd in history[:-1]:
        target = _target(cmd)
        if (_FILL_CMD.search(cmd) or _PATCH_CMD.search(cmd)) and target:
            last_write_target = target
            validated = False
            rendered = False
            continue
        if last_write_target and target == last_write_target:
            if _VALIDATE_CMD.search(cmd):
                validated = True
            if _RENDER_CMD.search(cmd):
                rendered = True

    if last_write_target is None:
        sys.exit(0)

    current_target = _target(command)
    current_is_write = bool(_FILL_CMD.search(command) or _PATCH_CMD.search(command))
    if current_is_write and current_target == last_write_target:
        # 同じ対象への追加fillは「まとめて後でvalidate/renderする」運用を妨げない
        sys.exit(0)
    if current_target == last_write_target and (_VALIDATE_CMD.search(command) or _RENDER_CMD.search(command)):
        sys.exit(0)

    missing = []
    if not validated:
        missing.append("waffle validate")
    if not rendered:
        missing.append("waffle render")
    if not missing:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[Hook] {last_write_target} をfill/patch-schemaで更新しましたが、"
                f"その後 {', '.join(missing)} を実行した形跡が見つからないまま次のコマンドに"
                f"進んでいます。document.jsonと成果物がズレたままにならないよう確認してください。"
            ),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

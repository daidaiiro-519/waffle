#!/usr/bin/env python3
"""process-reliability論点3: 配列fieldへのfill前にqueryを要求する（PreToolUse）。

Bash経由のwaffle scaffold fillが、配列型の値を含むvaluesを書き込もうとしている
とき、同一セッション内で同じpathに対してwaffle queryが先に呼ばれているかを
transcriptから確認する。「呼ばれたかどうか」自体は例外の無い構造的事実であり
（意図・合意の有無のような偽装可能な判定ではない）、Hook候補6の反省
（PreToolUse denyは構造的事実のみに使う）の対象外としてブロック方式を維持する。

CLAUDE.mdの運用ルール「配列はqueryで現在値取得→組み立て→fillで丸ごと置き換え」
を機械的に強制する。パースできない・確認できない場合は安全側（許可）に倒す。
"""
from __future__ import annotations

import json
import re
import sys

_FILL_CMD = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b")
_PATH_ARG = re.compile(r"--path\s+(\S+)")
_VALUES_ARG = re.compile(r"--values\s+'(.*)'\s*$", re.DOTALL)


def main() -> None:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    transcript_path = payload.get("transcript_path", "")

    if not _FILL_CMD.search(command):
        sys.exit(0)

    path_m = _PATH_ARG.search(command)
    values_m = _VALUES_ARG.search(command)
    if not path_m or not values_m:
        sys.exit(0)  # 想定外の形はパースせず許可する（安全側）

    target_path = path_m.group(1).strip("'\"")
    try:
        values = json.loads(values_m.group(1))
    except json.JSONDecodeError:
        sys.exit(0)

    has_array = isinstance(values, dict) and any(isinstance(v, list) for v in values.values())
    if not has_array:
        sys.exit(0)  # 配列フィールドを含まないfillは対象外

    if not transcript_path:
        sys.exit(0)  # transcriptを確認できない環境では許可する

    try:
        with open(transcript_path, encoding="utf-8") as f:
            transcript_text = f.read()
    except OSError:
        sys.exit(0)

    if "waffle query" in transcript_text and target_path in transcript_text:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"配列フィールドを含むfillです。{target_path} に対してこのセッション内で"
                "waffle queryを先に実行し、現在値を取得してから配列を組み立て直して"
                "ください（CLAUDE.mdの運用ルール: 配列はqueryで現在値取得→組み立て→"
                "fillで丸ごと置き換え）。"
            ),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

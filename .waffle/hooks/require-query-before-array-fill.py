#!/usr/bin/env python3
"""process-reliability論点3: 配列fieldへのfill前にqueryを要求する（PreToolUse）。

判定ロジック（クエリ先行の検証）はuc-check-query-precedes-array-fill（
CheckQueryPrecedesArrayFill）へ切り出し済み。このスクリプトは、Claude Code固有の
入出力（Bashコマンド文字列・セッションtranscriptファイル）を、そのusecaseが
受け取れる構造化された入力（targetPath/hasArrayValue/queriedPaths）へ翻訳し、
CLI経由で呼び出すだけの薄い駆動アダプター（Hexagonal Architectureの
Driving Adapter）である。新しい判定ロジックはここに持ち込まない。

「呼ばれたかどうか」自体は例外の無い構造的事実であり（意図・合意の有無のような
偽装可能な判定ではない）、Hook候補6の反省（PreToolUse denyは構造的事実のみに
使う）の対象外としてブロック方式を維持する。パースできない・確認できない場合は
安全側（許可）に倒す。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

_FILL_CMD = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b")
_PATH_ARG = re.compile(r"--path\s+(\S+)")
_VALUES_ARG = re.compile(r"--values\s+'(.*)'\s*$", re.DOTALL)
_QUERY_PATH = re.compile(r"waffle\s+query\b[^\n]*?--path\s+(\S+)")


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


def _extract_queried_paths(transcript_text: str) -> list[str]:
    return sorted({m.strip("'\"") for m in _QUERY_PATH.findall(transcript_text)})


def check(payload: dict, transcript_text: str | None = None) -> str | None:
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    if not _FILL_CMD.search(command):
        return None

    path_m = _PATH_ARG.search(command)
    values_m = _VALUES_ARG.search(command)
    if not path_m or not values_m:
        return None  # 想定外の形はパースせず許可する（安全側）

    target_path = path_m.group(1).strip("'\"")
    try:
        values = json.loads(values_m.group(1))
    except json.JSONDecodeError:
        return None

    has_array = isinstance(values, dict) and any(isinstance(v, list) for v in values.values())
    if not has_array:
        return None  # 配列フィールドを含まないfillは対象外

    if transcript_text is None:
        transcript_path = payload.get("transcript_path", "")
        if not transcript_path:
            return None  # transcriptを確認できない環境では許可する
        try:
            with open(transcript_path, encoding="utf-8") as f:
                transcript_text = f.read()
        except OSError:
            return None

    queried_paths = _extract_queried_paths(transcript_text)

    result = _run_waffle(
        "check-query-precedes-array-fill",
        "--target-path", target_path,
        "--has-array-value",
        "--queried-paths", json.dumps(queried_paths, ensure_ascii=False),
    )
    if result is None or result.get("allowed", True):
        return None  # usecase呼び出しに失敗した場合も安全側（許可）に倒す

    return result.get("reason") or (
        f"{target_path} に対してこのセッション内でwaffle queryを先に実行し、"
        "現在値を取得してから配列を組み立て直してください（CLAUDE.mdの運用ルール: "
        "配列はqueryで現在値取得→組み立て→fillで丸ごと置き換え）。"
    )


def main() -> None:
    payload = json.load(sys.stdin)
    reason = check(payload)
    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

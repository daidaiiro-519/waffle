#!/usr/bin/env python3
"""スキーマが書かれた直後に、指示の置かれ方の契約を確かめる（PostToolUse:Bash）。

守らせたいのは3つだけ。引く単位には x-prompt-query があること、値を書き込む欄には
x-prompt-write があること、そして契約が認める名前はこの2つだけであること。

新しい判定ロジックは一切持たない。既存の check-prompt-contract を呼ぶだけの薄い
ラッパー。判定を持たせると、検査とフックの2箇所を直すことになり、やがて食い違う。

スキーマへの正規の書き込み経路は waffle patch-schema だけなので、そこを見る。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# 書き込まれたschemaRefは、コマンド自身が名乗っている
_PATCH_SCHEMA = re.compile(
    r"waffle\s+patch-schema\b.*?--schema[-]?[Rr]ef\s+(\S+)")


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


def _describe(data: dict, schema_ref: str) -> list[str]:
    lines = []
    for entry in data.get("missing_query_prompts", []):
        lines.append(f"{entry['block']} に x-prompt-query がありません"
                     "（引く単位には読み方の指示が要ります）")
    for entry in data.get("missing_write_prompts", []):
        lines.append(f"{entry['path']} に x-prompt-write がありません"
                     "（値を書き込む欄には書き方の指示が要ります）")
    for entry in data.get("undeclared_prompt_keys", []):
        lines.append(f"{entry['at']} は契約に無い名前です"
                     "（使えるのは x-prompt-query と x-prompt-write の2つだけ）")
    return lines


def check(payload: dict) -> str | None:
    command = payload.get("tool_input", {}).get("command", "")
    match = _PATCH_SCHEMA.search(command)
    if not match:
        return None

    schema_ref = match.group(1).strip("'\"")
    data = _run_waffle("check-prompt-contract", "--schemaRef", schema_ref)
    if data is None:
        return (f"[Hook] {schema_ref} の指示の置かれ方を確かめられませんでした"
                "（検査を実行できていません）")
    if isinstance(data.get("error"), str):
        return f"[Hook] {schema_ref} の確認に失敗しました: {data['error']}"

    findings = _describe(data, schema_ref)
    if not findings:
        return None
    return (f"[Hook] {schema_ref} で、指示の置かれ方の契約が守られていません: "
            + " / ".join(findings))


def main() -> None:
    payload = json.load(sys.stdin)
    message = check(payload)
    if message:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

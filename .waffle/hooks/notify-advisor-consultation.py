#!/usr/bin/env python3
"""process-reliability論点1: advisor自動発火の信頼性（PostToolUse通知）。

Bash経由のwaffle scaffold create/fillが、advisorとの組み合わせが必須
（skill-routerのroutingTableでblock/nudge指定）なschema家族のdocumentを
作成・更新しようとしているとき、対応するadvisor Skillがこのセッション内で
呼ばれた形跡があるかをtranscriptから確認し、無ければ通知する（ブロックしない）。

「本当に相談したか」という意図の検証はPreToolUse denyでは信頼できない
（Hook候補6の反省）ため、PostToolUse通知に統一する。ハードコードした
ファイルパターン表を持たず、skill-routerのroutingTable document.jsonを
唯一の真実源としてCLI経由で毎回参照する（ddd-advisor/tech-lead-advisorの
共通指摘: 二重の真実源を作らない）。

qa-advisorは「評価はするが手を動かさない」という別種の特性を持ち、この
document編集ベースのトリガーには馴染まないため対象外（別途トリガー設計が必要、
process-reliability論点1の既知の未解決事項）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

_CREATE_CMD = re.compile(r"waffle\s+scaffold\s+--operation\s+create\b")
_FILL_CMD = re.compile(r"waffle\s+scaffold\s+--operation\s+fill\b")
_SCHEMA_REF_ARG = re.compile(r"--schemaRef\s+(\S+)")
_PATH_ARG = re.compile(r"--path\s+(\S+)")


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


def _schema_family(command: str) -> str | None:
    m = _SCHEMA_REF_ARG.search(command)
    if m:
        return m.group(1).strip("'\"").split("/")[0]
    m = _PATH_ARG.search(command)
    if not m:
        return None
    path = m.group(1).strip("'\"")
    meta = _run_waffle("query", "--operation", "get_meta", "--path", path)
    if not meta:
        return None
    schema_ref = meta.get("value", {}).get("schemaRef", "")
    return schema_ref.split("/")[0] if schema_ref else None


def check(payload: dict, transcript_text: str | None = None) -> str | None:
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")

    if not (_CREATE_CMD.search(command) or _FILL_CMD.search(command)):
        return None

    family = _schema_family(command)
    if not family:
        return None

    routing = _run_waffle(
        "query", "--operation", "query_path",
        "--path", ".waffle/documents/skills/skill-router.json",
        "--blockKey", "routingTable",
        "--expression", "@",
    )
    if not routing:
        return None
    rows = routing.get("value", {}).get("items", [])
    matched = [
        r for r in rows
        if family in r.get("purpose", "") and "qa-advisor" not in r.get("combinedSkills", [])
    ]
    if not matched:
        return None

    advisors: set[str] = set()
    max_strength = "nudge"
    for r in matched:
        advisors.update(r.get("combinedSkills", []))
        if r.get("strength") == "block":
            max_strength = "block"

    if transcript_text is None:
        transcript_path = payload.get("transcript_path", "")
        if not transcript_path:
            return None
        try:
            with open(transcript_path, encoding="utf-8") as f:
                transcript_text = f.read()
        except OSError:
            return None

    missing = sorted(a for a in advisors if a not in transcript_text)
    if not missing:
        return None

    tone = "必ず確認してください" if max_strength == "block" else "検討をおすすめします"
    return (
        f"[Hook] {family}系のdocumentを作成・更新していますが、"
        f"このセッション内で相談した形跡が見つからないadvisorがあります: "
        f"{', '.join(missing)}（skill-routerのroutingTableで{max_strength}指定）。{tone}。"
    )


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

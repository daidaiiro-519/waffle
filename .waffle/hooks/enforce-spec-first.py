#!/usr/bin/env python3
"""候補6: spec-first違反（spec無しでのschema実装着手）の禁止（PreToolUse）。

新規schemaファイル（src/waffle/domain/model/*/v*.json）を書こうとしたとき、
それを参照しstatus=VALIDATED以上のusecase specが.waffle/specs配下に
存在しなければ拒否する。「合意済み」の代替指標としてspec.statusを使う設計
（docs/brainstorm/brainstorm-waffle-hooks.md参照）。

既存schemaの更新（patch-schema等、CLI経由）はこのHookの対象外——このHookは
raw Edit/Writeでの新規schemaファイル作成のみを見る。
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

_TARGET = re.compile(r"src/waffle/domain/model/([^/]+)/v(\d+)\.json$")
_AGREED_STATUSES = {"VALIDATED", "RENDERED"}


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")

    m = _TARGET.search(file_path)
    if not m:
        sys.exit(0)

    schema_name, version = m.group(1), m.group(2)
    schema_ref = f"{schema_name}/v{version}"

    root = _project_root()
    matched_specs: list[tuple[str, str | None]] = []
    agreed = False
    for spec_path in glob.glob(os.path.join(root, ".waffle/documents/specs/**/*.json"), recursive=True):
        try:
            with open(spec_path, encoding="utf-8") as f:
                doc = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        text = json.dumps(doc, ensure_ascii=False)
        if schema_name in text:
            matched_specs.append((spec_path, doc.get("status")))
            if doc.get("status") in _AGREED_STATUSES:
                agreed = True

    if not agreed:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{schema_ref} を新規作成しようとしていますが、これを参照し"
                    f"status=VALIDATED以上のusecase specが見つかりません"
                    f"（該当spec: {[p for p, _ in matched_specs] or '0件'}）。"
                    "UDD原則に沿って先にspecを合意してください"
                    "（docs/brainstorm/配下でのブレストから始めること）。"
                ),
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

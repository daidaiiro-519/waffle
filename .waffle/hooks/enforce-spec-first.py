#!/usr/bin/env python3
"""候補6改訂: spec-first違反（spec無しでのschema実装着手）の通知（PostToolUse）。

新規schemaファイル（src/waffle/domain/model/*/v*.json）が書き込まれた後、
それを参照するstatus=VALIDATED以上のspecが.waffle/documents/specs配下に
見つからなければ、通知するだけ（ブロックしない）。

2026-07-13にPreToolUse（deny）として実装していたが、以下の理由で撤回・
書き直した（docs/brainstorm/brainstorm-waffle-hooks.md参照）:
- 「合意済みか」は tool_input の中身だけからは原理的に検証できない
  （AI自身が全ての証跡ファイルを書けてしまうため、どんな代替指標を
  採用しても自己申告の域を出ない）
- Waffleのschemaには「業務をモデリングするspec（usecaseが自然に対応する）」
  と「Waffle自身の運用を支えるインフラ・ツール系schema（usecaseを持つ
  必然性が無い）」の2種があり、後者では正当な理由でVALIDATED specが
  存在しないままschemaを書くケースが実在する（HandoffSchema導入時に発覚）
- 一方、Waffleは基本spec-first+TDDで実装しており、Gherkinシナリオ
  （AcceptanceScenarios等）はspecが正本のため、specが無ければAIは
  そもそも何を根拠にテストを書けばよいか分からず、自然にspecの有無を
  確認する動きになる（＝一次防御は既にプロセス自体に内蔵されている）
- ブロッキングは「それが無いと必ず困る」場面に限るべきで、それ以外は
  通知で足りる（通知を見ればAIは自身の振る舞いを見直せる）という運用方針

新規schema作成をブロックはしないが、レビュー時に拾える形の記録として
残すため、PostToolUseの通知に格下げした。
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
    matched_specs: list[str] = []
    agreed = False
    for spec_path in glob.glob(os.path.join(root, ".waffle/documents/specs/**/*.json"), recursive=True):
        try:
            with open(spec_path, encoding="utf-8") as f:
                doc = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        text = json.dumps(doc, ensure_ascii=False)
        if schema_name in text:
            matched_specs.append(os.path.relpath(spec_path, root))
            if doc.get("status") in _AGREED_STATUSES:
                agreed = True

    if not agreed:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"[Hook] {schema_ref} を新規作成しましたが、これを参照し"
                    f"status=VALIDATED以上のspecが見つかりません"
                    f"（該当spec: {matched_specs or '0件'}）。"
                    "spec-first原則（idea→ブレスト→spec→実装）に沿っているか確認してください"
                    "（Waffle自身のインフラ・運用系schemaはusecaseを持つ必然性が無いため、"
                    "正当な理由でこの通知が出ることもある）。"
                ),
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""PreToolUse:Bash集約ディスパッチャ。

protect-raw-json-access.py（Bash分岐）とrequire-query-before-array-fill.py
が、Bashコマンド1回ごとに個別のpython3プロセスとして起動していた
（tech-lead-advisor敵対的検証で指摘された実行時の重複）。

2本それぞれの判定関数をimportlib経由で動的importし、順に呼び出す。
いずれかが拒否理由を返した時点でそれ以降は呼ばず、即座にdenyを返す。
2本の判定基準・拒否理由の文言はこのファイルでは一切変更しない。新しい
判定ロジックはここに持ち込まない。protect-raw-json-access.pyのRead用
チェックはこのディスパッチャの対象外（PreToolUse:Readのmatcherが引き続き
protect-raw-json-access.py単体を呼ぶ）。
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(filename: str, modname: str) -> types.ModuleType:
    path = os.path.join(_HOOKS_DIR, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    payload = json.load(sys.stdin)

    protect_raw_json_access = _load("protect-raw-json-access.py", "_protect_raw_json_access")
    reason = protect_raw_json_access.check_bash(payload)

    if reason is None:
        require_query_before_array_fill = _load(
            "require-query-before-array-fill.py", "_require_query_before_array_fill"
        )
        reason = require_query_before_array_fill.check(payload)

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

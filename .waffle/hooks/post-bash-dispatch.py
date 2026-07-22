#!/usr/bin/env python3
"""PostToolUse:Bash集約ディスパッチャ。

check-drift-on-write.py・notify-advisor-consultation.py・
notify-validate-render-after-write.pyの3本がBashコマンド1回ごとに個別の
python3プロセスとして起動し、うち2本が同一のtranscriptファイルを独立に
全読みしていた（tech-lead-advisor敵対的検証で指摘された実行時の重複）。

3本それぞれのcheck()判定関数をimportlib経由で動的importし、transcript
ファイルを1回だけ読んでから渡す。3本の判定基準・通知文言はこのファイルでは
一切変更しない。新しい判定ロジックはここに持ち込まない。
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

    transcript_path = payload.get("transcript_path", "")
    transcript_text: str | None = None
    if transcript_path:
        try:
            with open(transcript_path, encoding="utf-8") as f:
                transcript_text = f.read()
        except OSError:
            transcript_text = None

    check_drift_on_write = _load("check-drift-on-write.py", "_check_drift_on_write")
    notify_advisor_consultation = _load("notify-advisor-consultation.py", "_notify_advisor_consultation")
    notify_validate_render_after_write = _load(
        "notify-validate-render-after-write.py", "_notify_validate_render_after_write"
    )

    messages = [
        check_drift_on_write.check(payload),
        notify_advisor_consultation.check(payload, transcript_text),
        notify_validate_render_after_write.check(payload, transcript_text),
    ]
    combined = "\n".join(m for m in messages if m)
    if combined:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": combined,
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

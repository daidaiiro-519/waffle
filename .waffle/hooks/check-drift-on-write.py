#!/usr/bin/env python3
"""候補2（testファイル側）・候補4: 書き込み直後のdrift自動発火（PostToolUse）。

書き込まれたファイルのパスパターンから、対応する既存driftチェックusecase
（check-usecase-class-drift / check-operation-drift / check-aggregate-class-drift /
check-domain-service-drift / check-scenario-drift）をCLI経由で自動実行し、
検出があったときだけ結果をモデルへ返す（クリーンなときは沈黙する——必要な
情報だけを返すという方針、docs/brainstorm/brainstorm-waffle-hooks.md参照）。

新しいdrift検知ロジックは一切持たない。既存usecaseをトリガーするだけの薄い
ラッパー。
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

_USECASE_IMPL = re.compile(r"src/waffle/application/usecases/.*\.py$")
_ENTITY_IMPL = re.compile(r"src/waffle/domain/entities/.*\.py$")
_SERVICE_IMPL = re.compile(r"src/waffle/domain/services/.*\.py$")
_TEST_FILE = re.compile(r"tests/(?:acceptance|integration)/(test_.*)\.py$")


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


def _has_findings(data: dict | None) -> bool:
    if data is None:
        return False
    return any(v for v in data.values() if isinstance(v, list) and v)


def _guess_spec_path(test_stem: str) -> str | None:
    # test_uc_check_aggregate_class_drift -> uc-check-aggregate-class-drift
    name = test_stem.removeprefix("test_").replace("_", "-")
    root = _project_root()
    matches = glob.glob(os.path.join(root, f".waffle/documents/specs/**/usecase/{name}.json"), recursive=True)
    return matches[0] if matches else None


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")

    reports: list[str] = []

    if _USECASE_IMPL.search(file_path):
        for cmd, label in [("check-usecase-class-drift", "usecase-class-drift"), ("check-operation-drift", "operation-drift")]:
            data = _run_waffle(cmd)
            if _has_findings(data):
                reports.append(f"[{label}] {json.dumps(data, ensure_ascii=False)}")

    if _ENTITY_IMPL.search(file_path):
        data = _run_waffle("check-aggregate-class-drift")
        if _has_findings(data):
            reports.append(f"[aggregate-class-drift] {json.dumps(data, ensure_ascii=False)}")

    if _SERVICE_IMPL.search(file_path):
        data = _run_waffle("check-domain-service-drift")
        if _has_findings(data):
            reports.append(f"[domain-service-drift] {json.dumps(data, ensure_ascii=False)}")

    m = _TEST_FILE.search(file_path)
    if m:
        spec_path = _guess_spec_path(m.group(1))
        if spec_path:
            rel_spec = os.path.relpath(spec_path, _project_root())
            data = _run_waffle("check-scenario-drift", "--specPath", rel_spec, "--testPath", file_path)
            if _has_findings(data):
                reports.append(f"[scenario-drift] {json.dumps(data, ensure_ascii=False)}")

    if reports:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"[Hook] {file_path} への書き込み後にdriftを検出しました: " + " / ".join(reports),
            }
        }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()

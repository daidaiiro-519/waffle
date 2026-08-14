#!/usr/bin/env python3
"""古い版のdocumentへの書き込みを、書き込む前に止める（PreToolUse:Bash）。

版ドリフトの検知自体はuc-check-schema-version-drift（CheckSchemaVersionDrift）が
既に持っている。欠けていたのは検知ではなく、検知結果が書き込みの前に読まれる
経路である。実際、最新版が既に切られ、運搬手段（scaffold --operation
migrate_schema）も存在していたにもかかわらず、古い版のdocumentへ延々と
fillし続けるということが起きた。しかもその版では廃止済みのブロックへ書いていた。

このスクリプトは、Claude Code固有の入力（Bashコマンド文字列）を、そのusecaseが
受け取れる形へ翻訳し、CLI経由で呼び出すだけの薄い駆動アダプター
（Hexagonal Architectureの Driving Adapter）である。新しい判定ロジックは
ここに持ち込まない——「その版が古いか」を決めるのは検査の側であって、この
ファイルではない。

「宣言された版が最新かどうか」は例外の無い構造的事実であり、意図や合意の有無の
ような偽装可能な判定ではないため、PreToolUse denyを使う。運搬そのもの
（migrate_schema）は当然この対象から外す。パースできない・確認できない場合は
安全側（許可）に倒す。
"""
from __future__ import annotations

import json
import os
import re
import subprocess

_WRITE_CMD = re.compile(r"waffle\s+(?:scaffold\s+--operation\s+fill|patch-schema)\b")
_MIGRATE_CMD = re.compile(r"--operation\s+migrate_schema\b")
_PATH_ARG = re.compile(r"--path\s+(\S+)")
_DOCS_ROOT = ".waffle/documents"


def _project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _outdated() -> dict[str, tuple[str, str]] | None:
    """検査に聞く。返すのは {文書のパス: (宣言された版, 最新の版)}。"""
    result = subprocess.run(
        ["uv", "run", "--project", ".", "waffle",
         "check-schema-version-drift", "--documentsRoot", _DOCS_ROOT],
        cwd=_project_root(), capture_output=True, text=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return {r["document"]: (r["schemaRef"], r["latest"])
            for r in report.get("outdated_references", [])}


def check(payload: dict) -> str | None:
    command = payload.get("tool_input", {}).get("command", "")

    if not _WRITE_CMD.search(command) or _MIGRATE_CMD.search(command):
        return None

    path_m = _PATH_ARG.search(command)
    if not path_m:
        return None  # 想定外の形はパースせず許可する（安全側）
    target = os.path.normpath(path_m.group(1).strip("'\""))

    outdated = _outdated()
    if outdated is None:
        return None  # 検査を動かせない環境では許可する

    hit = outdated.get(target)
    if hit is None:
        return None
    declared, latest = hit

    return (
        f"{target} が宣言している版は {declared} で、最新は {latest} です。"
        f"古い版には、最新版で廃止されたブロックが残っています。そこへ書き込むと、"
        f"消える予定の場所へ内容を足すことになります。\n"
        f"先に運んでください: "
        f"uv run waffle scaffold --operation migrate_schema --path {target} "
        f"--schemaRef {latest}"
    )

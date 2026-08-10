#!/usr/bin/env python3
"""セッション開始時（SessionStart）に、Orchestrator（agentRefsに"waffle"を含む
process種別knowledge）の要約を追加コンテキストとして注入する。

新しい検知ロジックは一切持たない。既存usecase（query-collectionのfilter_documents、
queryのquery_path）をCLI経由で呼ぶだけの薄いラッパー（check-drift-on-write.py等と
同じ規約）。CLAUDE.mdは一度アンビエントにロードされるだけで「今読みに行け」という
発火点を持たないため、都度フレッシュに評価されるHookを経路として持たせる
（docs/brainstorm/brainstorm-knowledge-kind-classification.md参照）。
"""
from __future__ import annotations

import json
import subprocess
import sys


def _project_root() -> str:
    import os

    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _run_cli(args: list[str]) -> dict | None:
    try:
        result = subprocess.run(
            ["uv", "run", "--project", _project_root(), "waffle", *args],
            capture_output=True, text=True, timeout=15, cwd=_project_root(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _filtered_paths(key: str, value: str) -> set[str] | None:
    """knowledge配下を1つの条件で絞り、該当したパスの集合を返す。

    Args:
        key: 絞り込みに使うトップレベルのフィールド名。
        value: そのフィールドが持つべき値。

    Returns:
        該当したdocumentのパスの集合。取得できなかった場合は None。

    Raises:
        なし。
    """
    filtered = _run_cli([
        "query-collection", "--operation", "filter_documents",
        "--path", ".waffle/documents/knowledge", "--key", key, "--value", value,
    ])
    if not filtered or "value" not in filtered:
        return None
    return set(filtered["value"].keys())


def _collect_summaries() -> list[str]:
    """Orchestrator宛の、採用済みknowledgeの要約を集める。

    下書きのまま置かれているものは注入しない。配布の経路がstatusを見ないと、
    審査を経ていない候補が採用済みのものと区別なく並び、下書きに留める意味が消える。

    Returns:
        「- パス: 概要」の形の行の並び。1件も無ければ空。

    Raises:
        なし。
    """
    for_orchestrator = _filtered_paths("agentRefs", "waffle")
    adopted = _filtered_paths("status", "ACTIVE")
    if for_orchestrator is None or adopted is None:
        return []

    summaries: list[str] = []
    for doc_path in sorted(for_orchestrator & adopted):
        text_result = _run_cli([
            "query", "--operation", "query_path", "--path", doc_path,
            "--blockKey", "description", "--expression", "text",
        ])
        if not text_result or not text_result.get("value"):
            continue
        summaries.append(f"- {doc_path}: {text_result['value']}")
    return summaries


def main() -> int:
    summaries = _collect_summaries()
    if not summaries:
        return 0

    context = (
        "生成・検証サイクルに関する横断的な方法論knowledge（domain種別ではなく、"
        "Orchestrator自身が進行管理・再検証の判断に使うべきもの）:\n"
        + "\n".join(summaries)
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

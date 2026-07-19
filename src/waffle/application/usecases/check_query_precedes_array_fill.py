"""check query precedes array fill — 配列fillの前に対象pathへのqueryが
先行しているかを機械的に判定する application use case。

外部依存を持たない純粋な判定ロジック（Bashコマンドの解析やセッションtranscriptの
読み込みといった技術的詳細は、駆動アダプター側（Hookスクリプト）の責務として
usecaseの外に留める）。
"""
from __future__ import annotations

from waffle.shared.result import Ok, Result


class CheckQueryPrecedesArrayFill:
    def run(self, target_path: str, has_array_value: bool, queried_paths: list[str]) -> Result[dict]:
        if has_array_value and target_path not in queried_paths:
            return Ok({
                "allowed": False,
                "reason": f"{target_path} への配列fillの前に、waffle queryで現在値を取得してください。",
            })
        return Ok({"allowed": True, "reason": None})

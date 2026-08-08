"""check query precedes array fill — 配列fillの前に対象pathへのqueryが
先行しているかを機械的に判定する application use case。

外部依存を持たない純粋な判定ロジック（Bashコマンドの解析やセッションtranscriptの
読み込みといった技術的詳細は、駆動アダプター側（Hookスクリプト）の責務として
usecaseの外に留める）。
"""
from __future__ import annotations

from waffle.shared.result import Ok, Result


class CheckQueryPrecedesArrayFill:
    """配列を書き込む前に、その道を読んでいたかを確かめる。"""
    def run(self, target_path: str, has_array_value: bool, queried_paths: list[str]) -> Result[dict]:
        """配列を書き込む前に、その道を読んでいたかを確かめる。

        Args:
            target_path: 走査する対象の置き場所。
            has_array_value: 書き込もうとしている値に配列が含まれるか。
            queried_paths: その書き込みより前に読み取りを済ませた道の一覧。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        if has_array_value and target_path not in queried_paths:
            return Ok({
                "allowed": False,
                "reason": f"{target_path} への配列fillの前に、waffle queryで現在値を取得してください。",
            })
        return Ok({"allowed": True, "reason": None})

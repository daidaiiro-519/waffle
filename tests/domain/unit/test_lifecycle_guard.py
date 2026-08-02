"""lifecycle_guard（schema の x-lifecycle を読む薄い guard）の補助的なテスト。

agg-document の invariantScenarios には対応しない。宣言されたシナリオに
紐づかないテストを同じファイルへ混ぜると、そのテストが常に孤立として
報告され続け、警報が意味を失うため別ファイルに置く。
"""
from waffle.domain.services.lifecycle_guard import next_status

_SCHEMA = {
    "x-lifecycle": {
        "transitions": [
            {"from": None, "to": "CREATED", "command": "create"},
            {"from": "CREATED", "to": "VALIDATED", "command": "validate"},
            {"from": "VALIDATED", "to": "RENDERED", "command": "render"},
            {"from": "VALIDATED", "to": "SUPERSEDED", "command": "supersede"},
        ]
    }
}


def test_legal_transition_returns_target():
    """宣言された遷移は遷移先の状態を返す。"""
    assert next_status(_SCHEMA, "CREATED", "validate") == "VALIDATED"


def test_schema_without_lifecycle_returns_none():
    """x-lifecycle を持たない schema では、どのコマンドも遷移しない。"""
    assert next_status({}, "ACTIVE", "validate") is None

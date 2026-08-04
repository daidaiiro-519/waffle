"""寄せられた反応の読み書きを、保管の上で実現する。

鍵は comments/{共有アーティファクトの識別子}/{寄せられた時刻}-{識別子}.json
の形で、先頭に時刻を持つ。こうしておくと鍵の順がそのまま寄せられた順になり、
並べ替えのために中身を読まなくて済む。

差し替えの区切りは鍵の末尾で見分ける。中身を読まずに数えられるので、一覧の
ように多くの共有アーティファクトを横断する場面で効く。並びに載せる形（kind）
とは別に、鍵の上にも同じ区別を持たせている。
"""
from __future__ import annotations

import json

DIVIDER_SUFFIX = "-replaced.json"


class StoredCommentRepository:
    def __init__(self, store):
        self._store = store

    def list_of(self, artifact_id: str) -> tuple[list[dict], int]:
        found, unreadable = [], 0
        for key in sorted(self._store.list(_prefix(artifact_id))):
            try:
                record = json.loads(self._store.get(key))
            except Exception:
                unreadable += 1
                continue
            record["id"] = _record_id(key)
            found.append(record)
        return found, unreadable

    def count_of(self, artifact_id: str) -> int:
        if not artifact_id:
            return 0
        return sum(1 for key in self._store.list(_prefix(artifact_id))
                   if not key.endswith(DIVIDER_SUFFIX))

    def add_replacement_divider(self, artifact_id: str, at: int) -> None:
        self._store.put(
            f"{_prefix(artifact_id)}{at}{DIVIDER_SUFFIX}",
            json.dumps({"kind": "divider", "postedAt": at}, ensure_ascii=False),
            "application/json",
        )


def _prefix(artifact_id: str) -> str:
    return f"comments/{artifact_id}/"


def _record_id(key: str) -> str:
    """鍵から、そのコメント1件を指す識別子を取り出す。返信先はこれで指される。"""
    return key.rsplit("/", 1)[-1].removesuffix(".json")

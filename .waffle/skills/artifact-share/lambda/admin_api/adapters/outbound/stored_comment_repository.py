"""寄せられた反応の読み書きを、保管の上で実現する。

鍵は comments/{共有アーティファクトの識別子}/{寄せられた時刻}-{識別子}.json
の形で、先頭に時刻を持つ。こうしておくと鍵の順がそのまま寄せられた順になり、
並べ替えのために中身を読まなくて済む。

差し替えの区切りは鍵の末尾で見分ける。中身を読まずに数えられるので、一覧の
ように多くの共有アーティファクトを横断する場面で効く。本文の中の値では
決めない——本文で決めていた時期に、閲覧者が嘘の区切りを差し込める穴があった。

保管の欄名と業務の語彙の対応を、ここだけが知る。保管は decision と呼び、業務は
判定（verdict）と呼ぶ。保管の欄名は変えない——コメントは追記しかされず書き直す
経路が構造として存在しないため、欄名を変えると既に書かれた判定が読めなくなり、
「投稿された後に常に変わらない」という不変条件を実装の側から破ることになる。
対応は infra/contract/comment-entries.json が両方の綴りで宣言する。
"""
from __future__ import annotations

import json

from domain.entities.comment import Comment
from domain.value_objects.comment import (
    COMMENT, DIVIDER, AuthorName, CommentBody, CommentId, EntryKind, Verdict,
)
from domain.value_objects.shared_artifact import ArtifactId

DIVIDER_SUFFIX = "-replaced.json"

# 保管の欄名 → 集約の属性。ここだけが両方の綴りを知る
STORED_VERDICT = "decision"


class StoredCommentRepository:
    """寄せられた反応を、保管の上で読み書きする。"""
    def __init__(self, store):
        self._store = store

    def list_of(self, artifact_id: str) -> tuple[list[Comment], int]:
        """1件の共有アーティファクトに寄せられた反応を並べる。

        Args:
            artifact_id: 対象の共有アーティファクトの識別子。

        Returns:
            反応の一覧と、読めなかった件数。

        Raises:
            なし。
        """
        found, unreadable = [], 0
        for key in sorted(self._store.list(_prefix(artifact_id))):
            try:
                found.append(_from_record(json.loads(self._store.get(key)),
                                          key, artifact_id))
            except Exception:
                unreadable += 1
        return found, unreadable

    def count_of(self, artifact_id: str) -> int:
        """1件の共有アーティファクトに寄せられた反応の数を数える。

        Args:
            artifact_id: 対象の共有アーティファクトの識別子。

        Returns:
            反応の数。差し替えの区切りは含めない。

        Raises:
            なし。
        """
        if not artifact_id:
            return 0
        return sum(1 for key in self._store.list(_prefix(artifact_id))
                   if not key.endswith(DIVIDER_SUFFIX))

    def add_replacement_divider(self, artifact_id: str, at: int) -> None:
        """中身を差し替えた区切りを、反応の並びへ挟む。

        Args:
            artifact_id: 対象の共有アーティファクトの識別子。
            at: 差し替えた時点。

        Returns:
            なし。

        Raises:
            なし。
        """
        self._store.put(
            f"{_prefix(artifact_id)}{at}{DIVIDER_SUFFIX}",
            json.dumps({"kind": DIVIDER, "postedAt": at}, ensure_ascii=False),
            "application/json",
        )


def _from_record(record: dict, key: str, artifact_id: str) -> Comment:
    """保管の記録を、業務の語彙を持つコメントへ直す。

    どちらの種別かは鍵の末尾で決める。本文の中の値では決めない。
    """
    divider = key.endswith(DIVIDER_SUFFIX)
    parent = record.get("parentId")
    return Comment(
        comment_id=CommentId(_record_id(key)),
        kind=EntryKind(DIVIDER if divider else COMMENT),
        target_artifact_id=ArtifactId(artifact_id),
        author=AuthorName(record.get("author") or ""),
        body=CommentBody(record.get("body") or ""),
        verdict=Verdict(record.get(STORED_VERDICT) or COMMENT),
        posted_at=str(record.get("postedAt", "")),
        parent_id=CommentId(parent) if parent else None,
    )


def _prefix(artifact_id: str) -> str:
    return f"comments/{artifact_id}/"


def _record_id(key: str) -> str:
    """鍵から、そのコメント1件を指す識別子を取り出す。返信先はこれで指される。"""
    return key.rsplit("/", 1)[-1].removesuffix(".json")

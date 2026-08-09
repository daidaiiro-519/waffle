"""閲覧者が共有アーティファクトに残したコメント1件。

誰が何を言い、どういう判定だったのかを守る。一貫性の境界は1件＝1回の書き込みで、
それより大きくならない——コメントは共有アーティファクトとは別に数え切れず増える
ため、共有アーティファクトの内側には置かない。符丁で指し示す関係に留める。

投稿された後は変わらない。名乗りだけで投稿できる以上、他人のコメントを書き換え
られる余地を残すと、記録そのものが信用できなくなる。だから状態を変えるメソッドを
持たない——変える道が無いことが、不変であることの実装そのものである。

残す操作（post）は閲覧の面が担い、区切りを残す操作（recordReplacement）は業務の
Lambda が担う。どちらも同じ並びに1件を追記する。この型は、その並びを読む側が
業務の語彙で扱うためにある。

対象の仕様: agg-comment
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.comment import (
    AuthorName, CommentBody, CommentId, EntryKind, Verdict,
)
from domain.value_objects.shared_artifact import ArtifactId


@dataclass(frozen=True)
class Comment:
    """閲覧者が残したコメント1件。差し替えの区切りも同じ形で並びに載る。"""

    comment_id: CommentId
    kind: EntryKind
    target_artifact_id: ArtifactId
    author: AuthorName
    body: CommentBody
    verdict: Verdict
    posted_at: str
    parent_id: CommentId | None = None

    def is_divider(self) -> bool:
        """差し替えの区切りか。

        Returns:
            区切りであれば True。

        Raises:
            なし。
        """
        return self.kind.is_divider()

    def replies_to(self, other: "Comment") -> bool:
        """その相手への返信として成立するか。

        返信先として指せるのは、同じ共有アーティファクトに付いたコメントだけ。
        別の共有アーティファクトのコメントへ返信できると、やり取りの筋道が
        読めなくなる。

        Args:
            other: 返信先として指そうとしている相手。

        Returns:
            返信として成立すれば True。

        Raises:
            なし。
        """
        return (self.parent_id is not None
                and self.parent_id == other.comment_id
                and self.target_artifact_id == other.target_artifact_id)

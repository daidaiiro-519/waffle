"""閲覧者が残したコメントが持つ値。

どれも書き換えられない。名乗るだけで誰でも残せる以上、あとから書き換えられる
余地を残すと、記録そのものが信用できなくなる。

対象の仕様: agg-comment
"""
from __future__ import annotations

from dataclasses import dataclass

# 並びに載る1件が、閲覧者のコメントなのか差し替えの区切りなのか
COMMENT = "comment"
DIVIDER = "divider"

# コメントに添える判定
JUST_AN_OPINION = "comment"   # ただの意見
APPROVED = "approve"          # この方向でよい
NEEDS_REVISION = "revise"     # 直してほしい


@dataclass(frozen=True)
class CommentId:
    """コメント1件を一意に指すID。

    投稿する側が投稿の瞬間に決める。他のコメントと重ならない。
    """

    value: str


@dataclass(frozen=True)
class AuthorName:
    """コメントを残した人の名乗り。

    あらかじめ登録された人物を指すものではなく、その場で名乗った文字列にすぎない。
    同じ名乗りが別人であることを妨げない。
    """

    value: str


@dataclass(frozen=True)
class CommentBody:
    """コメントの本文。

    常に文字として扱い、書かれた内容を組み立ての指示として解釈しない。誰でも
    投稿でき、しかも上書きできず残るため、ここが崩れると消せない仕掛けが残る。
    実際に文字として示すのは閲覧の面だが、この値がそう扱われるものであることは
    ここで表明する。
    """

    text: str


@dataclass(frozen=True)
class Verdict:
    """コメントに添える判定。

    ただの意見か、この方向でよいか、直してほしいかの3つのいずれか。添えられて
    いなければ、ただの意見として扱う。
    """

    value: str = JUST_AN_OPINION

    def is_approval(self) -> bool:
        """この方向でよい、という判定か。

        Returns:
            合意が示されていれば True。

        Raises:
            なし。
        """
        return self.value == APPROVED

    def asks_revision(self) -> bool:
        """直してほしい、という判定か。

        Returns:
            直しを求めていれば True。

        Raises:
            なし。
        """
        return self.value == NEEDS_REVISION


@dataclass(frozen=True)
class EntryKind:
    """並びに載る1件が、閲覧者のコメントなのか、差し替えの区切りなのか。

    閲覧者が残したものはコメント、中身の差し替えに伴って仕組みが残したものは
    区切りになる。区切りには名乗りも判定も無い。

    どちらであるかは鍵の末尾で決まり、本文の中の値では決めない——本文で決めて
    いた時期に、閲覧者が嘘の区切りを並びへ差し込める穴があった。
    """

    value: str = COMMENT

    def is_divider(self) -> bool:
        """差し替えの区切りか。

        Returns:
            区切りであれば True。

        Raises:
            なし。
        """
        return self.value == DIVIDER

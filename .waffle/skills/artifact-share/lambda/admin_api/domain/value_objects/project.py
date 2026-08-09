"""プロジェクトが持つ値。

どれも書き換えられない。出し入れの範囲だけは作るときに決めてあとから変えない
——変えられると、入れた人の前提が黙って崩れる。

対象の仕様: agg-project
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.identifier import PROJECT_ID_LENGTH, ensure

# 公開されているかどうか。共有アーティファクトと同じ語を使う
PUBLISHED = "PUBLISHED"
SUSPENDED = "SUSPENDED"

# 誰が共有アーティファクトを出し入れできるか
PERSONAL = "PERSONAL"   # 持ち主だけ
SHARED = "SHARED"       # 招かれた投稿者なら誰でも、自分のものを


def is_known_scope(scope: str) -> bool:
    """出し入れの範囲として認めている値か。

    Args:
        scope: 判定する出し入れの範囲。

    Returns:
        認めている値であれば True。

    Raises:
        なし。
    """
    return scope in (PERSONAL, SHARED)


@dataclass(frozen=True)
class ProjectId:
    """プロジェクトを一意に指す短いID。

    通る形は字種と桁数で決まる。作られ方によらずここで確かめる。
    """

    value: str

    def __post_init__(self) -> None:
        ensure(self.value, PROJECT_ID_LENGTH, "プロジェクトの識別子")


@dataclass(frozen=True)
class ProjectKey:
    """外の仕組みがこのプロジェクトを指すための、人が決める短い符丁。"""

    value: str = ""


@dataclass(frozen=True)
class ProjectOwner:
    """このプロジェクトを作った投稿者。"""

    value: str


@dataclass(frozen=True)
class ProjectScope:
    """誰が出し入れできるか。PERSONAL と SHARED のいずれか。

    作るときに決め、あとから変えられない。変えられると、入れた人の前提が
    黙って崩れる。
    """

    value: str

    def is_shared(self) -> bool:
        """招かれた投稿者なら誰でも出し入れしてよい範囲か。

        Returns:
            共有の範囲であれば True。

        Raises:
            なし。
        """
        return self.value == SHARED


@dataclass(frozen=True)
class ProjectStatus:
    """公開されているかどうか。PUBLISHED と SUSPENDED のいずれか。"""

    value: str

    def is_published(self) -> bool:
        """いま公開されているか。

        Returns:
            公開されていれば True。

        Raises:
            なし。
        """
        return self.value == PUBLISHED

    def is_suspended(self) -> bool:
        """いま公開を止めているか。

        Returns:
            止めていれば True。

        Raises:
            なし。
        """
        return self.value == SUSPENDED

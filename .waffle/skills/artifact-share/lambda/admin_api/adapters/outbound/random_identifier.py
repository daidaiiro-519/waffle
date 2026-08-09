"""推測できない並びを、実行環境が持つ予測できない値から作る。

環境から値を読むのはここだけ。業務の語彙の側は、どんな形なら通るかを決めるが、
どうやってその形の値を得るかは知らない。

連番にしないのは、識別子から他人のものを数え上げられないようにするため。
字種と桁数は業務の語彙の側が正本として持ち、ここはそれを読んで使う。

architecture: architecture-artifact-share の conceptPlacement（outbound-adapter）
"""
from __future__ import annotations

import secrets

from domain.value_objects.identifier import (
    ARTIFACT_ID_LENGTH, ID_ALPHABET, PROJECT_ID_LENGTH,
)
from domain.value_objects.project import ProjectId
from domain.value_objects.shared_artifact import ArtifactId
from domain.value_objects.view_token import (
    TOKEN_GROUP_LENGTH, TOKEN_GROUPS, TOKEN_ID_LENGTH, ViewTokenId,
)


class RandomIdGenerator:
    """推測できない並びから、業務の語彙が定める形の値を作る。"""

    def new_artifact_id(self) -> ArtifactId:
        """共有アーティファクトを1つ指す識別子を発行する。

        Returns:
            共有アーティファクトを1つ指す識別子。

        Raises:
            なし。
        """
        return ArtifactId(_chars(ARTIFACT_ID_LENGTH))

    def new_project_id(self) -> ProjectId:
        """プロジェクトを1つ指す識別子を発行する。

        Returns:
            プロジェクトを1つ指す識別子。

        Raises:
            なし。
        """
        return ProjectId(_chars(PROJECT_ID_LENGTH))

    def new_view_token_id(self) -> ViewTokenId:
        """1本の閲覧トークンを一覧で選ぶための識別子を発行する。

        Returns:
            一覧で選ぶための識別子。

        Raises:
            なし。
        """
        return ViewTokenId(_chars(TOKEN_ID_LENGTH))

    def new_view_token_secret(self) -> str:
        """渡す相手に見せる閲覧トークンそのものの値を発行する。

        Returns:
            渡す相手に見せる閲覧トークンそのものの値。

        Raises:
            なし。
        """
        return "-".join(_chars(TOKEN_GROUP_LENGTH) for _ in range(TOKEN_GROUPS))


def _chars(length: int) -> str:
    """読み間違えにくい字種から、推測できない並びを作る。"""
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(length))

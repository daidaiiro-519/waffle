"""推測できない並びを作る口。

識別子も閲覧トークンも、他人のものを数え上げられないことが前提にある。その
ために要るのは環境が持つ予測できない値で、これは実行環境に結びつく。だから
業務の語彙の側では作らず、この口を通す。

どんな形なら識別子として通るか（字種・桁数）は業務の語彙の側が正本として持ち、
この口はそれを満たす値を組み立てて返す。作る側に正本を置くと、その経路を通らない
値が素通りする。

検証で決まった値に固定できるようにするためにも口として持つ。時計と同じ形。

architecture: architecture-artifact-share の conceptPlacement（port）
"""
from __future__ import annotations

from typing import Protocol

from domain.value_objects.project import ProjectId
from domain.value_objects.shared_artifact import ArtifactId
from domain.value_objects.view_token import ViewTokenId


class IdGenerator(Protocol):
    """推測できない並びから、業務の語彙が定める形の値を作る。"""

    def new_artifact_id(self) -> ArtifactId:
        """共有アーティファクトを1つ指す識別子を発行する。"""
        ...

    def new_project_id(self) -> ProjectId:
        """プロジェクトを1つ指す識別子を発行する。"""
        ...

    def new_view_token_id(self) -> ViewTokenId:
        """1本の閲覧トークンを一覧で選ぶための識別子を発行する。"""
        ...

    def new_view_token_secret(self) -> str:
        """渡す相手に見せる閲覧トークンそのものの値を発行する。

        区切って読みやすくするのは、口頭やチャットで渡されることがあるため。
        照合できる形はこの値から別途作られ、こちらは控えない。
        """
        ...

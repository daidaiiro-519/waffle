"""閲覧の可否を判じる面へ、判じるための材料を渡す。

この面は別の実行環境にあり、こちらを呼び返せない。閲覧者が来たその場で、
渡してある材料だけを見て開けるかどうかを決める。だからここへ渡すのは
「いま開けてよいか」を判じ切れるだけのものでなければならない。

記録をどう並べるか、鍵をどう付けるかは実装が決める。並べ方は閲覧の面と共通の
取り決め（infra/contract/）として置かれており、実装がそれを読む。

architecture: architecture-artifact-share の conceptPlacement（outbound-adapter）
"""
from __future__ import annotations

from typing import Protocol

from domain.view_subject import ViewSubject


class ViewGatePort(Protocol):
    """閲覧の面へ、いま誰が開けるのかを渡す。"""

    def replace_grants(self, subject: ViewSubject, grants: list[tuple[str, int]]) -> None:
        """その対象を開けられる閲覧トークンを、この顔ぶれに置き換える。

        渡すのは（照合に使う形, 期限）の並び。1本ずつ足したり外したりするので
        はなく毎回すべてを渡すのは、閲覧の面がその時点の顔ぶれだけを見るため。
        足し引きの履歴は、公開する側が持つ。

        1本も無い並びを渡すと、誰も開けないが公開は止まっていない状態になる。
        止めたこととは別の意味を持つ。
        """
        ...

    def close(self, subject: ViewSubject) -> None:
        """その対象を、どの閲覧トークンでも開けないようにする。"""
        ...

    def fingerprint_of(self, token: str) -> str:
        """その閲覧トークンを、閲覧の面が照合に使う形へ変える。

        公開する側はこの形を控え、閲覧トークンそのものの値は残さない。作り方を
        この口が持つのは、控える形が向こうの面の認める形と一字一句同じでなければ
        ならないため——向こうと話す側が決めなければ、ずれても気づけない。
        """
        ...

    def set_membership(self, artifact_id: str, project_ids: list[str]) -> None:
        """その共有アーティファクトが、どのプロジェクトから開けるかを伝える。"""
        ...

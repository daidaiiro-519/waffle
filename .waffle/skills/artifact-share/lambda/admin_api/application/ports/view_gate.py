"""閲覧の可否を判じる面へ、判じるための材料を渡す。

この面は別の実行環境にあり、こちらを呼び返せない。閲覧者が来たその場で、
渡してある材料だけを見て開けるかどうかを決める。だからここへ渡すのは
「いま開けてよいか」を判じ切れるだけのものでなければならない。

記録をどう並べるか、鍵をどう付けるかは実装が決める。並べ方は閲覧の面と
共通の取り決め（infra/contract/）として置かれており、実装がそれを読む。

architecture: architecture-artifact-share の conceptPlacement（outbound-adapter）
"""
from __future__ import annotations

from typing import Protocol

from domain.view_subject import ViewSubject


class ViewGatePort(Protocol):
    """閲覧の面が判じるための材料を渡す。"""

    def allow(self, subject: ViewSubject, token: str, at: int,
              ttl: int = 0, generation: int = 1) -> None:
        """その対象を、この閲覧トークンで開けるようにする。

        閲覧トークンそのものの値は残さない。照合できる形だけを渡す。
        """
        ...

    def close(self, subject: ViewSubject) -> None:
        """その対象を、どの閲覧トークンでも開けないようにする。"""
        ...

    def generation_of(self, subject: ViewSubject) -> int:
        """いま何代目か。読めなければ1代目として扱う。"""
        ...

    def set_membership(self, artifact_id: str, project_ids: list[str]) -> None:
        """その共有アーティファクトが、どのプロジェクトから開けるかを伝える。"""
        ...

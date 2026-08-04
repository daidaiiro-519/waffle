"""閲覧の面へ、見えるものを置く。

集約の状態を残す場所ではない。ここに置くのは、閲覧者のブラウザが直接受け取る
成果物——中身そのものと、それを見せる画面、まとめの一覧である。だから
repository ではなく、別の口として分けてある。

画面の見た目（雛形・置き場所・URLの組み立て）は実装が決める。application は
「これを見せられる状態にする」としか言わない。

architecture: architecture-artifact-share の conceptPlacement（outbound-adapter）
"""
from __future__ import annotations

from typing import Protocol


class ViewerSitePort(Protocol):
    """閲覧の面への配置と、そこへの案内。"""

    def place_artifact(self, artifact_id: str, content: str, display_name: str) -> str:
        """中身と、それを見せる画面を置く。

        中身は書き換えずにそのまま置く。画面はこちらが組み立てる。
        使った画面の版を返す——あとで雛形を変えたときに、置き直しが要るものを
        見分けられるようにするため。
        """
        ...

    def replace_artifact_content(self, artifact_id: str, content: str) -> None:
        """中身だけを差し替える。共有URLも画面も変えない。"""
        ...

    def read_artifact_content(self, artifact_id: str) -> str:
        """置いてある中身を読む。読めなければ空。"""
        ...

    def place_project(self, project_id: str) -> None:
        """プロジェクトを見せる画面を置く。中身は一覧から読む。"""
        ...

    def place_project_listing(self, project_id: str, display_name: str,
                              artifacts: list[dict]) -> None:
        """プロジェクトに入っているものの一覧を置く。"""
        ...

    def artifact_url(self, artifact_id: str) -> str:
        """その共有アーティファクトを見てもらうための共有URL。"""
        ...

    def project_url(self, project_id: str) -> str:
        """そのプロジェクトを見てもらうための共有URL。"""
        ...

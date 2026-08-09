"""閲覧トークンで開ける対象。

共有アーティファクト1件と、プロジェクト1つの2種類がある。どちらも同じ形の
閲覧トークンで開き、同じように止められるが、指しているものは別なので取り違え
られないように種別を持たせる。

閲覧の面がこれをどう見分けるか（鍵の付け方）は、この値には現れない。

対象の仕様: agg-shared-artifact / agg-project
"""
from __future__ import annotations

from dataclasses import dataclass

ARTIFACT = "artifact"
PROJECT = "project"


@dataclass(frozen=True)
class ViewSubject:
    """閲覧トークンで開ける対象を1つ指す。"""

    kind: str
    id: str

    @staticmethod
    def artifact(artifact_id: str) -> "ViewSubject":
        """共有アーティファクト1件を指す対象を作る。

        Args:
            artifact_id: 指す共有アーティファクトの識別子。

        Returns:
            その1件を指す対象。

        Raises:
            なし。
        """
        return ViewSubject(ARTIFACT, artifact_id)

    @staticmethod
    def project(project_id: str) -> "ViewSubject":
        """プロジェクト1つを指す対象を作る。

        Args:
            project_id: 指すプロジェクトの識別子。

        Returns:
            その1つを指す対象。

        Raises:
            なし。
        """
        return ViewSubject(PROJECT, project_id)

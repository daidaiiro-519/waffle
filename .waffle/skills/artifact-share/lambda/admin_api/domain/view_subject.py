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
        return ViewSubject(ARTIFACT, artifact_id)

    @staticmethod
    def project(project_id: str) -> "ViewSubject":
        return ViewSubject(PROJECT, project_id)

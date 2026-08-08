"""要求が指している対象を読む。

受け口は「どちらの種別か」を決めない。決めているように見えても、それは
共有アーティファクトとプロジェクトのどちらを指すかという業務の判断であり、
受け口が持ってよいのは外からの入力を呼び出しの形へ移すことだけ。

判断をこちら側へ置くことで、受け口は application だけを知ればよくなる。

対象の仕様: agg-shared-artifact / agg-project
"""
from __future__ import annotations

from domain.view_subject import ViewSubject


def subject_from(body: dict) -> ViewSubject:
    """要求の中身から、閲覧トークンで開ける対象を1つ読む。

    プロジェクトの指定があればプロジェクト、無ければ共有アーティファクト。

    Args:
        body: 要求の中身。

    Returns:
        閲覧トークンで開ける対象。

    Raises:
        なし。
    """
    if body.get("projectId"):
        return ViewSubject.project(body["projectId"])
    return ViewSubject.artifact(body.get("artifactId", ""))

"""扱ってよいプロジェクトを取り出す。

「見せ方を変えられるか」と「出し入れできるか」は別の判定になる。前者は持ち主と
管理者だけ、後者は共有なら招かれた投稿者も含む。どちらの判定も集約自身が持ち、
ここが担うのは扱えないことをどう伝えるかだけ。
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from domain.project import Project
from shared.errors import ManageError, ProjectError

NOT_FOUND = "PROJECT_NOT_FOUND"


def read_index(projects: ProjectRepository, project_id: str) -> Project | None:
    """プロジェクトを読む。無ければ None。"""
    return projects.find(project_id)


def save_project(projects: ProjectRepository, clock: Clock, project: Project) -> Project:
    """更新した時点を刻んで残す。"""
    from dataclasses import replace
    stamped = replace(project, updated_at=clock())
    projects.save(stamped)
    return stamped


def require_own(projects: ProjectRepository, caller: Caller, project_id: str) -> Project:
    """見せ方を変えてよいプロジェクトを取り出す。持ち主か管理者だけ。"""
    project = projects.find(project_id)
    if project is None or not project.manageable_by(caller.id, caller.is_admin):
        raise ProjectError(NOT_FOUND, "見つかりません。")
    return project


def require_writable(projects: ProjectRepository, caller: Caller,
                     project_id: str) -> Project:
    """共有アーティファクトを出し入れしてよいプロジェクトを取り出す。

    個人のプロジェクトへ他人が入れようとしたときは、無いものと同じ拒み方に
    する——区別できると、存在そのものが読み取れてしまう。
    """
    project = projects.find(project_id)
    if project is None:
        raise ManageError(NOT_FOUND, "そのプロジェクトはありません。")
    if not project.status.is_published():
        raise ManageError("PROJECT_SUSPENDED", "そのプロジェクトは公開が止まっています。")
    if not project.accepts_membership_from(caller.id, caller.is_admin):
        raise ManageError(NOT_FOUND, "そのプロジェクトはありません。")
    return project

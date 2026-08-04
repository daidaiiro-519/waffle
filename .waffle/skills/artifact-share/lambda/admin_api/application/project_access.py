"""扱ってよいプロジェクトを取り出す。

読み出し（repository）と、扱ってよいかの判定（domain）と、扱えないことをどう
伝えるか（ここ）は別のことなので、それぞれの持ち場に置く。ここが担うのは最後の
1つだけ。

「見せ方を変えられるか」と「出し入れできるか」は別の判定になる。前者は持ち主と
管理者だけ、後者は共有なら招かれた投稿者も含む。複数の操作が同じ取り出し方を
するので、1か所に置く。
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from domain.publication import SHARED, is_published
from shared.errors import ManageError, ProjectError

NOT_FOUND = "PROJECT_NOT_FOUND"


def read_index(projects: ProjectRepository, project_id: str) -> dict | None:
    """プロジェクトの索引を読む。無ければ None。"""
    return projects.find(project_id)


def save_project(projects: ProjectRepository, clock: Clock, index: dict) -> None:
    index["updatedAt"] = clock()
    projects.save(index)


def require_own(projects: ProjectRepository, caller: Caller, project_id: str) -> dict:
    """見せ方を変えてよいプロジェクトの索引を読む。

    持ち主と管理者だけが通る。それ以外は、拒むのではなく見つからないものと
    して扱う。無いものと他人のものを同じ拒み方にすることで、そこに何かが
    あること自体を読み取らせない。
    """
    index = read_index(projects, project_id)
    if not index or not (caller.is_admin or index.get("owner") == caller.id):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    return index


def require_writable(projects: ProjectRepository, caller: Caller, project_id: str) -> dict:
    """共有アーティファクトを出し入れしてよいプロジェクトかを確かめる。

    共有なら招かれた投稿者なら誰でも、個人なら持ち主だけ。管理者は両方。
    見せ方を変える操作と違い、こちらは共有の別を見る。
    """
    index = read_index(projects, project_id)
    if not index:
        raise ManageError("PROJECT_NOT_FOUND", "そのプロジェクトはありません。")
    if not is_published(index):
        raise ManageError("PROJECT_SUSPENDED", "そのプロジェクトは公開が止まっています。")

    if caller.is_admin or index.get("owner") == caller.id:
        return index
    if index.get("scope") == SHARED:
        return index

    # 個人のプロジェクトへ他人が入れようとしている。
    # 無いものと同じ拒み方にして、存在を読み取らせない
    raise ManageError("PROJECT_NOT_FOUND", "そのプロジェクトはありません。")

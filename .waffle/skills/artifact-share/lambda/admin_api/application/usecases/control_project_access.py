"""まとめて渡した相手の範囲を、あとから絞り直す。

止めると、このプロジェクトの閲覧トークンでは何も開けなくなる。入っている共有
アーティファクトは、それぞれの閲覧トークンで引き続き開ける——プロジェクトは
見せ方の束ねであって、入れ物ではない。

閲覧トークンそのものの発行と無効化は、対象を問わず共通の操作として別に扱う。

対象の仕様: uc-control-project-access
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.project_access import require_own, save_project
from domain import view_token
from domain.publication import ACTIVE, DISABLED, is_published, is_suspended
from domain.view_subject import ViewSubject
from shared.errors import ProjectError


def suspend(projects: ProjectRepository, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """このプロジェクトの閲覧トークンでは何も開けない状態にする。

    入っている共有アーティファクトは、それぞれの閲覧トークンで引き続き開ける。
    プロジェクトは見せ方の束ねであって、入れ物ではない。
    """
    index = require_own(projects, caller, project_id)
    if not is_published(index):
        raise ProjectError("NOT_ACTIVE", "すでに公開が止まっています。")

    gate.close(ViewSubject.project(project_id))
    index["status"] = DISABLED
    save_project(projects, clock, index)

    return {"projectId": project_id, "status": DISABLED}


def resume(projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """再び開ける状態に戻す。

    止める前に渡していた閲覧トークンのうち、期限内で無効にしていないものを
    そのまま使える状態に戻す。
    """
    index = require_own(projects, caller, project_id)
    if not is_suspended(index):
        raise ProjectError("NOT_SUSPENDED", "公開は止まっていません。")

    now = clock()
    gate.replace_grants(ViewSubject.project(project_id),
                        view_token.grants(index.get("viewTokens"), now))
    index["status"] = ACTIVE
    save_project(projects, clock, index)

    return {"projectId": project_id,
            "url": viewer.project_url(project_id),
            "status": ACTIVE}

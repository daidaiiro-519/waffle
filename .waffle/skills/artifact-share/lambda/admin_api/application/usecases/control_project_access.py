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
from domain.project import PUBLISHED, SUSPENDED
from domain.view_subject import ViewSubject
from shared.errors import ProjectError


def _suspend(projects: ProjectRepository, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """このプロジェクトの閲覧トークンでは何も開けない状態にする。

    入っている共有アーティファクトは、それぞれの閲覧トークンで引き続き開ける。
    プロジェクトは見せ方の束ねであって、入れ物ではない。
    """
    project = require_own(projects, caller, project_id)
    if not project.status.is_published():
        raise ProjectError("NOT_ACTIVE", "すでに公開が止まっています。")

    gate.close(ViewSubject.project(project_id))
    save_project(projects, clock, project.suspended(clock()))

    return {"projectId": project_id, "status": SUSPENDED}


def _resume(projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """再び開ける状態に戻す。

    止める前に渡していた閲覧トークンのうち、期限内で無効にしていないものを
    そのまま使える状態に戻す。
    """
    project = require_own(projects, caller, project_id)
    if not project.status.is_suspended():
        raise ProjectError("NOT_SUSPENDED", "公開は止まっていません。")

    now = clock()
    gate.replace_grants(ViewSubject.project(project_id),
                        view_token.grants(project.view_tokens, now))
    save_project(projects, clock, project.resumed(now))

    return {"projectId": project_id,
            "url": viewer.project_url(project_id),
            "status": PUBLISHED}


class ControlProjectAccess:
    """まとめて渡した相手の範囲を、あとから絞り直す。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock) -> None:
        self._projects = projects
        self._viewer = viewer
        self._gate = gate
        self._clock = clock

    def run(self, operation: str, caller: Caller, project_id: str) -> dict:
        """このユースケースの唯一の入口。"""
        if operation == "suspend":
            return _suspend(self._projects, self._gate, self._clock, caller, project_id)
        if operation == "resume":
            return _resume(self._projects, self._viewer, self._gate, self._clock, caller, project_id)
        raise ValueError(f"知らない操作です: {operation}")

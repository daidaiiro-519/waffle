"""関わりのある共有アーティファクトを、1つの閲覧トークンでまとめて見せられるように
する。

作った人が持ち主になる。個人か共有かはあとから変えられない——変えられると、
入れた人の前提が黙って崩れるため。

対象の仕様: uc-create-project
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.project_access import save_project
from application.viewer_listing import place_project_page, write_listing
from domain import view_token
from domain.identifier import new_project_id
from domain.publication import ACTIVE, is_known_scope
from domain.view_subject import ViewSubject
from shared.errors import ProjectError

# 作ったときに最初に発行される1本の名前。あとから名前を付けて増やせる
FIRST_TOKEN_NAME = "最初の共有"


def create(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, display_name: str, scope: str, project_key: str = "") -> dict:
    """プロジェクトを作り、閲覧トークンを発行する。作った時点では何も入っていない。

    共有の別はここでしか決まらない。変える操作を用意しないことが、
    「作ったあと変わらない」という決めごとを守る手立てそのものになる。
    """
    name = (display_name or "").strip()
    if not name:
        raise ProjectError("NAME_REQUIRED", "表示名を入力してください。")
    if not is_known_scope(scope):
        raise ProjectError("SCOPE_REQUIRED", "個人か共有かを選んでください。")

    project_id = new_project_id()
    token = view_token.new_token()
    now = clock()
    first = view_token.issued(view_token.new_token_id(), FIRST_TOKEN_NAME,
                              gate.fingerprint_of(token),
                              view_token.expires_at(now), now)

    index = {
        "projectId": project_id,
        "displayName": name,
        "projectKey": (project_key or "").strip(),
        "owner": caller.id,
        "scope": scope,
        "status": ACTIVE,
        "memberArtifactIds": [],
        "viewTokens": [first],
        "createdAt": now,
    }
    save_project(projects, clock, index)
    place_project_page(viewer, project_id)
    write_listing(artifacts, viewer, index)

    # 閲覧の面へ渡すのは最後。ここまで成功して初めて開ける状態になる
    gate.replace_grants(ViewSubject.project(project_id),
                        view_token.grants([first], now))

    return {"projectId": project_id, "token": token, "tokenShownOnce": True,
            "url": viewer.project_url(project_id), "name": name, "scope": scope,
            "event": "ProjectCreated"}

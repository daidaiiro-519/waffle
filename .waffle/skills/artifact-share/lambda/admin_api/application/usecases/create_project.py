"""関わりのある共有アーティファクトを、1つの閲覧トークンでまとめて見せられるように
する。

作った人が持ち主になる。個人か共有かはあとから変えられない——変えられると、
入れた人の前提が黙って崩れるため。

対象の仕様: uc-create-project
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.identifier import IdGenerator
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.project_access import save_project
from application.viewer_listing import place_project_page, write_listing
from domain.value_objects import view_token
from domain.value_objects.project import (
    PUBLISHED,
    ProjectKey,
    is_known_scope,
    ProjectOwner,
    ProjectScope,
    ProjectStatus,
)
from domain.entities.project import Project
from domain.value_objects.view_subject import ViewSubject
from shared.errors import ProjectError

# 作ったときに最初に発行される1本の名前。あとから名前を付けて増やせる
FIRST_TOKEN_NAME = "最初の共有"



@dataclass(frozen=True)
class CreatedProject:
    """作った結果。最初の1本の閲覧トークンは、この一度きり示される。"""

    project_id: str
    token: str
    url: str
    name: str
    scope: str
    token_shown_once: bool = True

def _create(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, ids: IdGenerator, caller: Caller, display_name: str, scope: str, project_key: str = "") -> CreatedProject:
    """プロジェクトを作り、閲覧トークンを発行する。作った時点では何も入っていない。

    共有の別はここでしか決まらない。変える操作を用意しないことが、
    「作ったあと変わらない」という決めごとを守る手立てそのものになる。
    """
    name = (display_name or "").strip()
    if not name:
        raise ProjectError("NAME_REQUIRED", "表示名を入力してください。")
    if not is_known_scope(scope):
        raise ProjectError("SCOPE_REQUIRED", "個人か共有かを選んでください。")

    project_id = ids.new_project_id()
    token = ids.new_view_token_secret()
    now = clock()
    first = view_token.issued(ids.new_view_token_id(), FIRST_TOKEN_NAME,
                              gate.fingerprint_of(token),
                              view_token.expires_at(now), now)

    project = Project(
        project_id=project_id,
        display_name=name,
        project_key=ProjectKey((project_key or "").strip()),
        status=ProjectStatus(PUBLISHED),
        owner=ProjectOwner(caller.id),
        scope=ProjectScope(scope),
        created_at=now,
        view_tokens=(first,),
        updated_at=now,
    )
    save_project(projects, clock, project)
    place_project_page(viewer, project_id.value)
    write_listing(artifacts, projects, viewer, project)

    # 閲覧の面へ渡すのは最後。ここまで成功して初めて開ける状態になる
    gate.replace_grants(ViewSubject.project(project_id.value),
                        view_token.grants((first,), now))

    return CreatedProject(project_id=project_id.value, token=token,
                          url=viewer.project_url(project_id.value), name=name, scope=scope)


class CreateProject:
    """関わりのある共有アーティファクトを、1つの閲覧トークンでまとめて見せられるように

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, ids: IdGenerator) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._viewer = viewer
        self._gate = gate
        self._clock = clock
        self._ids = ids

    def run(self, caller: Caller, display_name: str, scope: str, project_key: str = "") -> CreatedProject:
        """このユースケースの唯一の入口。"""
        return _create(self._artifacts, self._projects, self._viewer, self._gate, self._clock, self._ids, caller, display_name, scope, project_key)

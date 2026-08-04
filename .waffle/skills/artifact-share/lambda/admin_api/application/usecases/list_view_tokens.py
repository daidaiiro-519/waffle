"""いま誰に見せているかを確かめ、外したいものを選ぶ。

名前と期限を返し、閲覧トークンそのものの値は返さない。値は発行した瞬間に一度
だけ示され、以後は見返せない。

対象の仕様: uc-list-view-tokens
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.view_token_access import (ViewTokenError, require_manageable_subject,
                                           save_tokens)
from domain import view_token
from domain.view_subject import ViewSubject



def _list_tokens(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                clock: Clock, caller: Caller, subject: ViewSubject) -> dict:
    """いま渡している相手を確かめる。閲覧トークンそのものの値は返さない。"""
    record = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    return {"viewTokens": [
        {"tokenId": t["tokenId"], "name": t.get("name", ""),
         "expiresAt": t.get("expiresAt", view_token.NO_EXPIRY),
         "issuedAt": t.get("issuedAt", 0)}
        for t in view_token.active_tokens(record.get("viewTokens"), now)]}


class ListViewTokens:
    """いま誰に見せているかを確かめ、外したいものを選ぶ。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._clock = clock

    def run(self, caller: Caller, subject: ViewSubject) -> dict:
        """このユースケースの唯一の入口。"""
        return _list_tokens(self._artifacts, self._projects, self._clock, caller, subject)

"""いま誰に見せているかを確かめ、外したいものを選ぶ。

名前と期限を返し、閲覧トークンそのものの値は返さない。値は発行した瞬間に一度
だけ示され、以後は見返せない。

対象の仕様: uc-list-view-tokens
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.view_token_access import (ViewTokenError, require_manageable_subject,
                                           save_tokens)
from domain.value_objects import view_token
from domain.value_objects.view_subject import ViewSubject




@dataclass(frozen=True)
class ViewTokenRow:
    """一覧の1行。閲覧トークンそのものの値は持たない。"""

    token_id: str
    name: str
    expires_at: int
    issued_at: int


@dataclass(frozen=True)
class ViewTokens:
    """いま渡している相手の一覧。"""

    view_tokens: tuple[ViewTokenRow, ...]

def _list_tokens(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                clock: Clock, caller: Caller, subject: ViewSubject) -> ViewTokens:
    """いま渡している相手を確かめる。閲覧トークンそのものの値は返さない。"""
    target = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    return ViewTokens(view_tokens=tuple(
        ViewTokenRow(token_id=t.token_id.value, name=t.name,
                     expires_at=t.expires_at.value, issued_at=t.issued_at)
        for t in view_token.usable(target.view_tokens, now)))


class ListViewTokens:
    """いま誰に見せているかを確かめ、外したいものを選ぶ。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._clock = clock

    def run(self, caller: Caller, subject: ViewSubject) -> ViewTokens:
        """このユースケースの唯一の入口。"""
        return _list_tokens(self._artifacts, self._projects, self._clock, caller, subject)

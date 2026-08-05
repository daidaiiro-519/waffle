"""見せたい相手ごとに別々の閲覧トークンを渡し、あとから個別に外せるようにする。

それまでの閲覧トークンはどれも無効にしない。増やすたびに前のものが切れては、
相手ごとに渡すという目的を果たさない。

対象の仕様: uc-issue-view-token
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

from application.view_token_access import (DUPLICATE_TOKEN_NAME, EXPIRY_TOO_FAR,
                                           TOKEN_LIMIT_REACHED)


def _issue(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          gate: ViewGatePort, clock: Clock, caller: Caller, subject: ViewSubject,
          name: str, ttl: int | None = None) -> dict:
    """閲覧トークンを1本増やし、その値を一度だけ返す。

    それまでの閲覧トークンはどれも無効にしない。相手ごとに別々に渡せることが
    この操作の目的であり、増やすたびに前のものが切れては目的を果たさない。
    """
    target = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(target.view_tokens, now)

    if not view_token.within_active_limit(tokens, now):
        raise ViewTokenError(
            TOKEN_LIMIT_REACHED,
            f"同時に渡せる閲覧トークンは{view_token.MAX_ACTIVE}本までです。"
            "どれかを無効にしてから発行してください。")
    if not view_token.name_is_free(tokens, name, now):
        raise ViewTokenError(DUPLICATE_TOKEN_NAME,
                             "その名前は既に使っています。別の名前を付けてください。")

    expiry = view_token.expires_at(now, ttl)
    if not view_token.within_expiry_limit(subject.kind, now, expiry):
        raise ViewTokenError(
            EXPIRY_TOO_FAR,
            "期限が遠すぎます。共有アーティファクトの閲覧トークンは1ヶ月までです。")

    token = view_token.new_token()
    issued = view_token.issued(name, gate.fingerprint_of(token), expiry, now)
    tokens = tokens + (issued,)

    save_tokens(artifacts, projects, clock, subject, target, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))

    return {"tokenId": issued.token_id.value, "name": name, "token": token,
            "expiresAt": expiry.value, "tokenShownOnce": True}


class IssueViewToken:
    """見せたい相手ごとに別々の閲覧トークンを渡し、あとから個別に外せるようにする。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, projects: ProjectRepository, gate: ViewGatePort, clock: Clock) -> None:
        self._artifacts = artifacts
        self._projects = projects
        self._gate = gate
        self._clock = clock

    def run(self, caller: Caller, subject: ViewSubject, name: str, ttl: int | None = None) -> dict:
        """このユースケースの唯一の入口。"""
        return _issue(self._artifacts, self._projects, self._gate, self._clock, caller, subject, name, ttl)

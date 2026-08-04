"""ある相手にだけ見せるのをやめる。他の相手はそのまま見られるようにしておく。

対象の公開は止めない。1本を外すために他の相手まで巻き添えで外れると、外す操作が
使いにくくなり、結局使われなくなる。

対象の仕様: uc-revoke-view-token
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

from application.view_token_access import TOKEN_NOT_FOUND


def revoke(artifacts: SharedArtifactRepository, projects: ProjectRepository,
           gate: ViewGatePort, clock: Clock, caller: Caller, subject: ViewSubject,
           token_id: str) -> dict:
    """その1本だけを使えなくする。他の相手はそのまま見られる。"""
    record = require_manageable_subject(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(record.get("viewTokens"), now)

    if all(t.get("tokenId") != token_id for t in tokens):
        raise ViewTokenError(TOKEN_NOT_FOUND, "その閲覧トークンはありません。")

    tokens = view_token.revoked(tokens, token_id)
    save_tokens(artifacts, projects, clock, record, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return {"tokenId": token_id, "revoked": True}

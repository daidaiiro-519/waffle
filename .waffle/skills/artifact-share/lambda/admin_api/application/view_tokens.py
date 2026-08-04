"""閲覧トークンの発行・一覧・無効化。

共有アーティファクトとプロジェクトのどちらにも同じ形で渡すため、対象の種別で
分けずに1つの場所へ置く。仕様も「閲覧トークンそのものの発行と無効化は、対象を
問わず共通の操作として別に扱う」と定めている。

置き場所は種別ごとに違う（共有アーティファクトは自身の記録、プロジェクトは
その索引）ので、読み書きだけを種別で振り分ける。

対象の仕様: uc-issue-view-token / uc-list-view-tokens / uc-revoke-view-token /
uc-revoke-all-view-tokens
"""
from __future__ import annotations

from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from domain import view_token
from domain.publication import manageable_by
from domain.view_subject import ARTIFACT, ViewSubject
from shared.errors import ApplicationError

TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
TOKEN_LIMIT_REACHED = "TOKEN_LIMIT_REACHED"
DUPLICATE_TOKEN_NAME = "DUPLICATE_TOKEN_NAME"
EXPIRY_TOO_FAR = "EXPIRY_TOO_FAR"


class ViewTokenError(ApplicationError):
    """閲覧トークンを扱えない。"""


def issue(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          gate: ViewGatePort, clock: Clock, caller: Caller, subject: ViewSubject,
          name: str, ttl: int | None = None) -> dict:
    """閲覧トークンを1本増やし、その値を一度だけ返す。

    それまでの閲覧トークンはどれも無効にしない。相手ごとに別々に渡せることが
    この操作の目的であり、増やすたびに前のものが切れては目的を果たさない。
    """
    record = _load(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(record.get("viewTokens"), now)

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
    tokens.append(view_token.issued(view_token.new_token_id(), name,
                                    gate.fingerprint_of(token), expiry, now))

    _save(artifacts, projects, clock, record, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))

    return {"tokenId": tokens[-1]["tokenId"], "name": name, "token": token,
            "expiresAt": expiry, "tokenShownOnce": True}


def list_tokens(artifacts: SharedArtifactRepository, projects: ProjectRepository,
                clock: Clock, caller: Caller, subject: ViewSubject) -> dict:
    """いま渡している相手を確かめる。閲覧トークンそのものの値は返さない。"""
    record = _load(artifacts, projects, caller, subject)
    now = clock()
    return {"viewTokens": [
        {"tokenId": t["tokenId"], "name": t.get("name", ""),
         "expiresAt": t.get("expiresAt", view_token.NO_EXPIRY),
         "issuedAt": t.get("issuedAt", 0)}
        for t in view_token.active_tokens(record.get("viewTokens"), now)]}


def revoke(artifacts: SharedArtifactRepository, projects: ProjectRepository,
           gate: ViewGatePort, clock: Clock, caller: Caller, subject: ViewSubject,
           token_id: str) -> dict:
    """その1本だけを使えなくする。他の相手はそのまま見られる。"""
    record = _load(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(record.get("viewTokens"), now)

    if all(t.get("tokenId") != token_id for t in tokens):
        raise ViewTokenError(TOKEN_NOT_FOUND, "その閲覧トークンはありません。")

    tokens = view_token.revoked(tokens, token_id)
    _save(artifacts, projects, clock, record, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return {"tokenId": token_id, "revoked": True}


def revoke_all(artifacts: SharedArtifactRepository, projects: ProjectRepository,
               gate: ViewGatePort, clock: Clock, caller: Caller,
               subject: ViewSubject) -> dict:
    """渡した相手を一度にすべて外す。公開そのものは止めない。"""
    record = _load(artifacts, projects, caller, subject)
    now = clock()
    tokens = view_token.without_expired(record.get("viewTokens"), now)
    revoked_count = len(view_token.active_tokens(tokens, now))

    tokens = view_token.all_revoked(tokens, now)
    _save(artifacts, projects, clock, record, tokens)
    gate.replace_grants(subject, view_token.grants(tokens, now))
    return {"revoked": revoked_count}


# ── 置き場所の振り分け ──────────────────────────────────

def _load(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          caller: Caller, subject: ViewSubject) -> dict:
    """扱ってよい対象を取り出す。扱えないものは見つからないものとして扱う。"""
    if subject.kind == ARTIFACT:
        record = artifacts.find(subject.id)
        allowed = record is not None and manageable_by(record, caller)
    else:
        record = projects.find(subject.id)
        allowed = record is not None and (
            caller.is_admin or record.get("owner") == caller.id)

    if not allowed:
        raise ViewTokenError(TARGET_NOT_FOUND, "見つかりません。")
    return record


def _save(artifacts: SharedArtifactRepository, projects: ProjectRepository,
          clock: Clock, record: dict, tokens: list[dict]) -> None:
    record["viewTokens"] = tokens
    record["updatedAt"] = clock()
    if "artifactId" in record:
        artifacts.save(record)
    else:
        projects.save(record)

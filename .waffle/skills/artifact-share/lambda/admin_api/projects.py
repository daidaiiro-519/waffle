"""プロジェクトを作り、その見せ方を変える。

複数の共有アーティファクトを1つの閲覧トークンでまとめて見せる単位を扱う。
作る・閲覧トークンの再発行・公開停止・再開を担い、中身の出し入れ（加える・
外す）は manage.py が持つ。

分けているのは、2つの判定が別物だからである。見せ方を変えてよいかは
「持ち主か管理者か」で決まり、出し入れしてよいかは「そのアーティファクトの
投稿者か」と「共有か持ち主か」で決まる。同じファイルに置くと、どちらの
判定を通ったのかが読めなくなる。

個人と共有の別は、閲覧の可否ではなく書き換えの可否である。したがって
閲覧ゲートはこの別を知らず、トークンの保管にも置かない。

対象の仕様: uc-create-project / uc-control-project-access
引き継ぎ: handoff-project-scope
"""

from __future__ import annotations

import json

from shared.errors import ManageError, ProjectError
from application.ports import Caller, Clock
from application.ports.project_repository import ProjectRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from domain.identifier import new_project_id
from domain.publication import (ACTIVE, DISABLED, PERSONAL, SHARED,
                                is_known_scope, is_published, is_suspended)
from domain.view_subject import ViewSubject
from domain import view_token

# 作ったときに最初に発行される1本の名前。あとから名前を付けて増やせる
FIRST_TOKEN_NAME = "最初の共有"


# 誰が共有アーティファクトを出し入れできるか


# ── 索引の読み書き ──────────────────────────────────────

def read_index(projects: ProjectRepository, project_id: str) -> dict | None:
    """プロジェクトの索引を読む。無ければ None。"""
    return projects.find(project_id)


def _write_index(projects: ProjectRepository, clock: Clock, index: dict) -> None:
    index["updatedAt"] = clock()
    projects.save(index)


def _read_own(projects: ProjectRepository, caller: Caller, project_id: str) -> dict:
    """見せ方を変えてよいプロジェクトの索引を読む。

    持ち主と管理者だけが通る。それ以外は、拒むのではなく見つからないものと
    して扱う。無いものと他人のものを同じ拒み方にすることで、そこに何かが
    あること自体を読み取らせない。
    """
    index = read_index(projects, project_id)
    if not index or not (caller.is_admin or index.get("owner") == caller.id):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    return index


# ── 一覧ページの書き出し ────────────────────────────────

def write_listing(artifacts: SharedArtifactRepository, viewer: ViewerSitePort, index: dict) -> None:
    """閲覧者が見る一覧の中身を書き出す。

    雛形（index.html）はどのプロジェクトでも同じものを置き、この中身
    （index.json）だけがプロジェクトごとに変わる。雛形を直したときは
    全プロジェクトへ置き直す（CLIの反映の手順が担う）。

    共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
    表示名が変わったときにも書き直す必要がある。
    """
    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        meta = artifacts.find(artifact_id)
        if meta is None:
            continue
        if not is_published(meta):
            continue          # 止まっているものは並べない（開けないため）
        rows.append({
            "artifactId": artifact_id,
            "name": meta.get("name", ""),
            "docType": meta.get("docType", ""),
            "description": meta.get("description", ""),
            "updatedAt": meta.get("updatedAt", 0),
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    viewer.place_project_listing(index["projectId"], index.get("displayName", ""), rows)


def _write_page(viewer: ViewerSitePort, project_id: str) -> None:
    """一覧ページを置く。中身は別に置く一覧から読む。"""
    viewer.place_project(project_id)


# ── 作る ────────────────────────────────────────────────

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
    _write_index(projects, clock, index)
    _write_page(viewer, project_id)
    write_listing(artifacts, viewer, index)

    # 閲覧の面へ渡すのは最後。ここまで成功して初めて開ける状態になる
    gate.replace_grants(ViewSubject.project(project_id),
                        view_token.grants([first], now))

    return {"projectId": project_id, "token": token, "tokenShownOnce": True,
            "url": viewer.project_url(project_id), "name": name, "scope": scope,
            "event": "ProjectCreated"}


# ── 見せ方を変える ──────────────────────────────────────


def suspend(projects: ProjectRepository, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """このプロジェクトの閲覧トークンでは何も開けない状態にする。

    入っている共有アーティファクトは、それぞれの閲覧トークンで引き続き開ける。
    プロジェクトは見せ方の束ねであって、入れ物ではない。
    """
    index = _read_own(projects, caller, project_id)
    if not is_published(index):
        raise ProjectError("NOT_ACTIVE", "すでに公開が止まっています。")

    gate.close(ViewSubject.project(project_id))
    index["status"] = DISABLED
    _write_index(projects, clock, index)

    return {"projectId": project_id, "status": DISABLED}


def resume(projects: ProjectRepository, viewer: ViewerSitePort, gate: ViewGatePort, clock: Clock, caller: Caller, project_id: str) -> dict:
    """再び開ける状態に戻す。

    止める前に渡していた閲覧トークンのうち、期限内で無効にしていないものを
    そのまま使える状態に戻す。
    """
    index = _read_own(projects, caller, project_id)
    if not is_suspended(index):
        raise ProjectError("NOT_SUSPENDED", "公開は止まっていません。")

    now = clock()
    gate.replace_grants(ViewSubject.project(project_id),
                        view_token.grants(index.get("viewTokens"), now))
    index["status"] = ACTIVE
    _write_index(projects, clock, index)

    return {"projectId": project_id,
            "url": viewer.project_url(project_id),
            "status": ACTIVE}


# ── 一覧 ────────────────────────────────────────────────

def list_projects(projects: ProjectRepository, caller: Caller) -> dict:
    """出し入れできるプロジェクトを並べる。閲覧トークンは含めない。

    自分が持ち主のものと、共有のものが並ぶ。管理者には全部が並ぶ。
    共有のものを並べるのは、そこへ自分のものを入れられるため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。黙って
    落とすと、作ったはずのプロジェクトが消えたように見える。
    """
    found, unreadable = projects.all()
    rows = []
    for index in found:
        mine = index.get("owner") == caller.id
        if not (caller.is_admin or mine or index.get("scope") == SHARED):
            continue
        rows.append({
            "projectId": index.get("projectId", ""),
            "name": index.get("displayName", ""),
            "projectKey": index.get("projectKey", ""),
            "scope": index.get("scope", PERSONAL),
            "status": index.get("status", ""),
            "owner": index.get("owner", ""),
            "isMine": mine,
            "artifactCount": len(index.get("memberArtifactIds", [])),
            "updatedAt": index.get("updatedAt", 0),
        })
    return {"projects": sorted(rows, key=lambda r: r["updatedAt"], reverse=True),
            "unreadable": unreadable}


# ── 中身を見る ──────────────────────────────────────────

def detail(artifacts: SharedArtifactRepository, projects: ProjectRepository, viewer: ViewerSitePort, caller: Caller, project_id: str) -> dict:
    """プロジェクトと、いま入っている共有アーティファクトを返す。

    見られるのは、そこへ自分のものを出し入れできる人（持ち主・管理者・
    共有なら招かれた投稿者）。入れるには、いま何が入っているかが
    見えている必要がある。

    公開が止まっていても見られる。止めたものを再開するか外すかを決めるのに
    中身が要るため。閲覧トークンは含めない。
    """
    index = read_index(projects, project_id)
    if not index:
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    if not (caller.is_admin or index.get("owner") == caller.id
            or index.get("scope") == SHARED):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")

    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        meta = artifacts.find(artifact_id)
        if meta is None:
            continue
        rows.append({
            "artifactId": artifact_id,
            "name": meta.get("name", ""),
            "docType": meta.get("docType", ""),
            "status": meta.get("status", ""),
            "uploadedBy": meta.get("uploadedBy", ""),
            "isMine": meta.get("uploadedBy") == caller.id,
            "updatedAt": meta.get("updatedAt", 0),
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    return {
        "project": {
            "projectId": index.get("projectId", ""),
            "name": index.get("displayName", ""),
            "projectKey": index.get("projectKey", ""),
            "scope": index.get("scope", PERSONAL),
            "status": index.get("status", ""),
            "owner": index.get("owner", ""),
            "isMine": index.get("owner") == caller.id,
            "url": viewer.project_url(project_id),
        },
        "artifacts": rows,
    }


# ── 出し入れの可否（manage.py から使う） ────────────────

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

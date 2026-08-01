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

from manage import Caller, Deps, ManageError
from publish import ID_ALPHABET, new_token, token_record

import secrets

# 誰が共有アーティファクトを出し入れできるか
PERSONAL = "PERSONAL"      # 持ち主だけ
SHARED = "SHARED"          # 招かれた投稿者なら誰でも、自分のものを
SCOPES = (PERSONAL, SHARED)

PROJECT_ID_LENGTH = 6


class ProjectError(Exception):
    """操作できない理由を、仕様のエラーコードとともに伝える。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def new_project_id() -> str:
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(PROJECT_ID_LENGTH))


# ── 索引の読み書き ──────────────────────────────────────

def _index_key(project_id: str) -> str:
    return f"projects/{project_id}.json"


def read_index(deps: Deps, project_id: str) -> dict | None:
    """プロジェクトの索引を読む。無ければ None。"""
    try:
        return json.loads(deps.store.get(_index_key(project_id)))
    except Exception:
        return None


def _write_index(deps: Deps, index: dict) -> None:
    index["updatedAt"] = deps.now()
    deps.store.put(_index_key(index["projectId"]),
                   json.dumps(index, ensure_ascii=False), "application/json")


def _read_own(deps: Deps, caller: Caller, project_id: str) -> dict:
    """見せ方を変えてよいプロジェクトの索引を読む。

    持ち主と管理者だけが通る。それ以外は、拒むのではなく見つからないものと
    して扱う。無いものと他人のものを同じ拒み方にすることで、そこに何かが
    あること自体を読み取らせない。
    """
    index = read_index(deps, project_id)
    if not index or not (caller.is_admin or index.get("owner") == caller.id):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    return index


def _viewer_url(deps: Deps, project_id: str) -> str:
    domain = deps.viewer_domain or "{viewer-domain}"
    return f"https://{domain}/proj/{project_id}/"


# ── 一覧ページの書き出し ────────────────────────────────

def write_listing(deps: Deps, index: dict) -> None:
    """閲覧者が見る一覧の中身を書き出す。

    雛形（index.html）はどのプロジェクトでも同じものを置き、この中身
    （index.json）だけがプロジェクトごとに変わる。雛形を直したときは
    全プロジェクトへ置き直す（CLIの反映の手順が担う）。

    共有アーティファクトの表示名を含むため、所属が変わったときだけでなく
    表示名が変わったときにも書き直す必要がある。
    """
    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        try:
            meta = json.loads(deps.store.get(f"meta/{artifact_id}.json"))
        except Exception:
            continue
        if meta.get("status") != "active":
            continue          # 止まっているものは並べない（開けないため）
        rows.append({
            "artifactId": artifact_id,
            "name": meta.get("name", ""),
            "docType": meta.get("docType", ""),
            "description": meta.get("description", ""),
            "updatedAt": meta.get("updatedAt", 0),
        })
    rows.sort(key=lambda r: r["updatedAt"], reverse=True)

    deps.store.put(
        f"proj/{index['projectId']}/index.json",
        json.dumps({"name": index.get("displayName", ""), "artifacts": rows},
                   ensure_ascii=False),
        "application/json",
    )


def _write_page(deps: Deps, project_id: str) -> None:
    """一覧ページの雛形を置く。中身は index.json から読む。"""
    page = (deps.project_page or "").replace("{{プロジェクトID}}", project_id)
    deps.store.put(f"proj/{project_id}/index.html", page, "text/html; charset=utf-8")


# ── 作る ────────────────────────────────────────────────

def create(deps: Deps, caller: Caller, display_name: str,
           scope: str, project_key: str = "") -> dict:
    """プロジェクトを作り、閲覧トークンを発行する。作った時点では何も入っていない。

    共有の別はここでしか決まらない。変える操作を用意しないことが、
    「作ったあと変わらない」という決めごとを守る手立てそのものになる。
    """
    name = (display_name or "").strip()
    if not name:
        raise ProjectError("NAME_REQUIRED", "表示名を入力してください。")
    if scope not in SCOPES:
        raise ProjectError("SCOPE_REQUIRED", "個人か共有かを選んでください。")

    project_id = new_project_id()
    token = new_token()
    now = deps.now()

    index = {
        "projectId": project_id,
        "displayName": name,
        "projectKey": (project_key or "").strip(),
        "owner": caller.id,
        "scope": scope,
        "status": "active",
        "memberArtifactIds": [],
        "createdAt": now,
    }
    _write_index(deps, index)
    _write_page(deps, project_id)
    write_listing(deps, index)

    # 閲覧トークンは最後に書く。ここまで成功して初めて開ける状態になる
    deps.keys.put(f"proj:{project_id}", token_record(token, now))

    return {"projectId": project_id, "token": token, "tokenShownOnce": True,
            "url": _viewer_url(deps, project_id), "name": name, "scope": scope,
            "event": "ProjectCreated"}


# ── 見せ方を変える ──────────────────────────────────────

def _generation(deps: Deps, project_id: str) -> int:
    try:
        record = deps.keys.get(f"proj:{project_id}")
    except Exception:
        return 1
    if record == "DISABLED":
        return 1
    parts = record.split("|")
    return int(parts[2]) if len(parts) > 2 else 1


def _issue(deps: Deps, project_id: str, generation: int) -> str:
    token = new_token()
    deps.keys.put(f"proj:{project_id}",
                  token_record(token, deps.now(), generation=generation))
    return token


def reissue_token(deps: Deps, caller: Caller, project_id: str) -> dict:
    """新しい閲覧トークンを発行し、それまでのものを使えなくする。URLは変えない。"""
    index = _read_own(deps, caller, project_id)
    generation = _generation(deps, project_id) + 1
    token = _issue(deps, project_id, generation)
    _write_index(deps, index)

    return {"projectId": project_id, "token": token, "tokenShownOnce": True,
            "url": _viewer_url(deps, project_id), "generation": generation}


def suspend(deps: Deps, caller: Caller, project_id: str) -> dict:
    """このプロジェクトの閲覧トークンでは何も開けない状態にする。

    入っている共有アーティファクトは、それぞれの閲覧トークンで引き続き開ける。
    プロジェクトは見せ方の束ねであって、入れ物ではない。
    """
    index = _read_own(deps, caller, project_id)
    if index.get("status") != "active":
        raise ProjectError("NOT_ACTIVE", "すでに公開が止まっています。")

    deps.keys.put(f"proj:{project_id}", "DISABLED")
    index["status"] = "disabled"
    _write_index(deps, index)

    return {"projectId": project_id, "status": "disabled"}


def resume(deps: Deps, caller: Caller, project_id: str) -> dict:
    """再び開ける状態に戻す。閲覧トークンは必ず新しくなる。"""
    index = _read_own(deps, caller, project_id)
    if index.get("status") != "disabled":
        raise ProjectError("NOT_SUSPENDED", "公開は止まっていません。")

    generation = _generation(deps, project_id) + 1
    token = _issue(deps, project_id, generation)
    index["status"] = "active"
    _write_index(deps, index)

    return {"projectId": project_id, "token": token, "tokenShownOnce": True,
            "url": _viewer_url(deps, project_id), "generation": generation,
            "status": "active"}


# ── 一覧 ────────────────────────────────────────────────

def list_projects(deps: Deps, caller: Caller) -> list[dict]:
    """出し入れできるプロジェクトを並べる。閲覧トークンは含めない。

    自分が持ち主のものと、共有のものが並ぶ。管理者には全部が並ぶ。
    共有のものを並べるのは、そこへ自分のものを入れられるため。
    """
    rows = []
    for key in deps.store.list("projects/"):
        try:
            index = json.loads(deps.store.get(key))
        except Exception:
            continue
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
    return sorted(rows, key=lambda r: r["updatedAt"], reverse=True)


# ── 中身を見る ──────────────────────────────────────────

def detail(deps: Deps, caller: Caller, project_id: str) -> dict:
    """プロジェクトと、いま入っている共有アーティファクトを返す。

    見られるのは、そこへ自分のものを出し入れできる人（持ち主・管理者・
    共有なら招かれた投稿者）。入れるには、いま何が入っているかが
    見えている必要がある。

    公開が止まっていても見られる。止めたものを再開するか外すかを決めるのに
    中身が要るため。閲覧トークンは含めない。
    """
    index = read_index(deps, project_id)
    if not index:
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")
    if not (caller.is_admin or index.get("owner") == caller.id
            or index.get("scope") == SHARED):
        raise ProjectError("PROJECT_NOT_FOUND", "見つかりません。")

    rows = []
    for artifact_id in index.get("memberArtifactIds", []):
        try:
            meta = json.loads(deps.store.get(f"meta/{artifact_id}.json"))
        except Exception:
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
            "url": _viewer_url(deps, project_id),
        },
        "artifacts": rows,
    }


# ── 出し入れの可否（manage.py から使う） ────────────────

def require_writable(deps: Deps, caller: Caller, project_id: str) -> dict:
    """共有アーティファクトを出し入れしてよいプロジェクトかを確かめる。

    共有なら招かれた投稿者なら誰でも、個人なら持ち主だけ。管理者は両方。
    見せ方を変える操作と違い、こちらは共有の別を見る。
    """
    index = read_index(deps, project_id)
    if not index:
        raise ManageError("PROJECT_NOT_FOUND", "そのプロジェクトはありません。")
    if index.get("status") != "active":
        raise ManageError("PROJECT_SUSPENDED", "そのプロジェクトは公開が止まっています。")

    if caller.is_admin or index.get("owner") == caller.id:
        return index
    if index.get("scope") == SHARED:
        return index

    # 個人のプロジェクトへ他人が入れようとしている。
    # 無いものと同じ拒み方にして、存在を読み取らせない
    raise ManageError("PROJECT_NOT_FOUND", "そのプロジェクトはありません。")

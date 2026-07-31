"""公開したあとの管理操作。

一覧・差し替え・トークンの再発行・公開停止・再開・プロジェクトへの出し入れを担う。
呼ぶのは、Cognitoで本人確認を通った投稿者だけ。手元のCLIは環境の構築だけを担当し、
ここには関わらない（保管を直接操作する経路を作らないため）。

投稿者は自分が公開したものだけを扱える。他人が公開したものは、拒むのではなく
「見つからない」として扱う。拒み方の違いで、そこに何かがあること自体が
分かってしまうのを避けるため。

管理者は全員のものを一覧・公開停止・再開・再発行でき、投稿者を移せる。
ただし差し替えだけは投稿者本人に限る。他人の中身が黙って入れ替わると、
集まったコメントが何に対する反応かが、投稿者の知らないうちに変わるため。

対象の仕様:
  uc-replace-content / uc-reissue-view-token / uc-suspend-artifact /
  uc-resume-artifact / uc-assign-to-project / uc-transfer-artifact
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Callable

from publish import inspect_html, new_token, token_record


class ManageError(Exception):
    """操作できない理由を、仕様のエラーコードとともに伝える。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Caller:
    """操作している人。誰であるかと、管理者かどうかだけを持つ。"""

    id: str
    is_admin: bool = False


@dataclass
class Deps:
    """外部との接点。実物の組み立ては handler が行う。

    store      保管の読み書き（put/get/list）。削除は持たない
    keys       トークンの保管の読み書き（put/get）
    directory  招かれている人の名簿（find/invite/remove）。この文脈の外にある
    now        現在時刻（エポック秒）。検証で固定できるようにする
    """

    store: object
    keys: object
    directory: object = None
    now: Callable[[], int] = lambda: int(time.time())
    viewer_domain: str = ""


# ── 索引の読み書き ──────────────────────────────────────

def _meta_key(artifact_id: str) -> str:
    return f"meta/{artifact_id}.json"


def _read_meta(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """扱ってよい索引を読む。扱えないものは見つからないものとして扱う。

    投稿者は自分が公開したもの、管理者は全員のものを扱える。
    """
    try:
        meta = json.loads(deps.store.get(_meta_key(artifact_id)))
    except Exception as e:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。") from e

    if not caller.is_admin and meta.get("uploadedBy") != caller.id:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")
    return meta


def _write_meta(deps: Deps, meta: dict) -> None:
    meta["updatedAt"] = deps.now()
    deps.store.put(_meta_key(meta["artifactId"]),
                   json.dumps(meta, ensure_ascii=False), "application/json")


def _viewer_url(deps: Deps, artifact_id: str) -> str:
    domain = deps.viewer_domain or "{viewer-domain}"
    return f"https://{domain}/p/{artifact_id}/"


def _require_published(meta: dict) -> None:
    if meta.get("status") != "active":
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")


# ── 一覧 ────────────────────────────────────────────────

def list_artifacts(deps: Deps, caller: Caller) -> list[dict]:
    """扱えるものを新しい順に並べる。トークンは含めない。

    投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。
    誰が公開したかを添えるのは、管理者が引き継ぎ先を決めるのに要るため。
    """
    rows = []
    for key in deps.store.list("meta/"):
        try:
            meta = json.loads(deps.store.get(key))
        except Exception:
            continue
        if not caller.is_admin and meta.get("uploadedBy") != caller.id:
            continue
        rows.append({
            "artifactId": meta.get("artifactId", ""),
            "name": meta.get("name", ""),
            "status": meta.get("status", ""),
            "docType": meta.get("docType", ""),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "projects": meta.get("projects", []),
            "uploadedBy": meta.get("uploadedBy", ""),
            "updatedAt": meta.get("updatedAt", 0),
        })
    return sorted(rows, key=lambda r: r["updatedAt"], reverse=True)


# ── 差し替え ────────────────────────────────────────────

def replace_content(deps: Deps, caller: Caller, artifact_id: str, html: str) -> dict:
    """中身だけを入れ替える。URL・トークン・これまでの反応は保つ。

    入れ替えた時点を区切りとして反応の並びに残す。これより前の指摘が
    入れ替え前のものだと読み取れるようにするため。
    """
    meta = _read_meta(deps, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id:
        # 管理者であっても他人の中身には手を出せない。集まったコメントが
        # 何に対する反応かを、投稿者の知らないうちに変えないため。
        # ここで「見つからない」と返さないのは、管理者は一覧でその存在を
        # 既に知っており、嘘になるから
        raise ManageError("NOT_THE_PUBLISHER",
                          "中身を差し替えられるのは、公開した本人だけです。")
    _require_published(meta)

    if not html or not html.strip():
        raise ManageError("EMPTY_CONTENT", "中身が空です。")

    found = inspect_html(html)
    now = deps.now()

    deps.store.put(f"p/{artifact_id}/content.html", html, "text/html; charset=utf-8")

    # 差し替えの区切り。反応と同じ並びに載る1件の記録として残す
    deps.store.put(
        f"comments/{artifact_id}/{now}-replaced.json",
        json.dumps({"kind": "divider", "postedAt": now}, ensure_ascii=False),
        "application/json",
    )

    if found["detected"]:
        meta.update({
            "docType": found["docType"],
            "documentId": found["documentId"],
            "description": found["description"],
            "tags": found["tags"],
        })
    meta["externalRefs"] = found["externalRefs"]
    _write_meta(deps, meta)

    return {"artifactId": artifact_id, "url": _viewer_url(deps, artifact_id),
            "externalRefs": found["externalRefs"]}


# ── トークンの再発行 ────────────────────────────────────

def _generation(deps: Deps, artifact_id: str) -> int:
    try:
        record = deps.keys.get(f"token:{artifact_id}")
    except Exception:
        return 1
    if record == "DISABLED":
        return 1
    parts = record.split("|")
    return int(parts[2]) if len(parts) > 2 else 1


def _issue(deps: Deps, artifact_id: str, generation: int) -> str:
    token = new_token()
    deps.keys.put(f"token:{artifact_id}",
                  token_record(token, deps.now(), generation=generation))
    return token


def reissue_token(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """新しいトークンを発行し、それまでのものを失効させる。URLは変えない。"""
    meta = _read_meta(deps, caller, artifact_id)
    generation = _generation(deps, artifact_id) + 1
    token = _issue(deps, artifact_id, generation)
    _write_meta(deps, meta)

    return {"artifactId": artifact_id, "token": token,
            "url": _viewer_url(deps, artifact_id), "generation": generation,
            "tokenShownOnce": True}


# ── 停止と再開 ──────────────────────────────────────────

def suspend(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """公開を止める。中身も反応も消さない。"""
    meta = _read_meta(deps, caller, artifact_id)
    _require_published(meta)

    deps.keys.put(f"token:{artifact_id}", "DISABLED")
    meta["status"] = "disabled"
    _write_meta(deps, meta)

    return {"artifactId": artifact_id, "status": "disabled"}


def resume(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """再び開けるようにする。トークンは必ず新しくなる。

    止める理由の多くは見せる相手を絞り直すことにあるため、止める前の
    トークンを復活させない。
    """
    meta = _read_meta(deps, caller, artifact_id)
    if meta.get("status") != "disabled":
        raise ManageError("NOT_SUSPENDED", "公開は止まっていません。")

    generation = _generation(deps, artifact_id) + 1
    token = _issue(deps, artifact_id, generation)
    meta["status"] = "active"
    _write_meta(deps, meta)

    return {"artifactId": artifact_id, "token": token,
            "url": _viewer_url(deps, artifact_id), "generation": generation,
            "status": "active", "tokenShownOnce": True}


# ── 引き継ぎ ────────────────────────────────────────────

def transfer(deps: Deps, caller: Caller, artifact_id: str, to_publisher: str) -> dict:
    """投稿者を別の投稿者へ移す。手入れできる人が替わるだけの操作。

    共有URL・閲覧トークン・中身・コメント・公開状態のいずれも変えない。
    渡した相手の手元で何かが変わると、投稿者の異動という内輪の事情が
    閲覧者に漏れる。

    公開停止中のものも移せる。止まっているものこそ引き継ぎ先が要る。
    """
    if not caller.is_admin:
        # 自分のものを他人へ押し付ける経路と、他人のものを自分のものに
        # する経路の両方を、ここひとつで塞ぐ
        raise ManageError("NOT_ADMINISTRATOR", "投稿者を移せるのは管理者だけです。")

    meta = _read_meta(deps, caller, artifact_id)

    if not (deps.directory and deps.directory.find(to_publisher)):
        # 招かれていない人へ移すと、その場で誰も手入れできない状態に戻る
        raise ManageError("PUBLISHER_NOT_FOUND", "移す先が招かれていません。")

    previous = meta.get("uploadedBy", "")
    meta["uploadedBy"] = to_publisher
    _write_meta(deps, meta)

    return {"artifactId": artifact_id, "from": previous, "to": to_publisher,
            "event": "ArtifactTransferred"}


# ── プロジェクトへの出し入れ ────────────────────────────

def _write_membership(deps: Deps, artifact_id: str, projects: list[str]) -> None:
    """所属を、関門が読める形へ書き出す。"""
    deps.keys.put(f"pp:{artifact_id}", " ".join(projects))


def assign(deps: Deps, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """まとめて見せる単位へ加える。人の明示的な操作でのみ成立する。"""
    meta = _read_meta(deps, caller, artifact_id)
    try:
        deps.keys.get(f"proj:{project_id}")
    except Exception as e:
        raise ManageError("PROJECT_NOT_FOUND", "そのプロジェクトはありません。") from e

    projects = list(meta.get("projects") or [])
    if project_id not in projects:              # 重ねて加えても二重にならない
        projects.append(project_id)
    meta["projects"] = projects
    _write_meta(deps, meta)
    _write_membership(deps, artifact_id, projects)

    return {"artifactId": artifact_id, "projects": projects}


def unassign(deps: Deps, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """まとめから外す。アーティファクト自体は個別のトークンで開けるまま残る。"""
    meta = _read_meta(deps, caller, artifact_id)
    projects = [p for p in (meta.get("projects") or []) if p != project_id]
    meta["projects"] = projects
    _write_meta(deps, meta)
    _write_membership(deps, artifact_id, projects)

    return {"artifactId": artifact_id, "projects": projects}

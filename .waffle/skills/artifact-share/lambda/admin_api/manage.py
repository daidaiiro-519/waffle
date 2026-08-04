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

from ports import Caller, ArtifactStore, Clock, PublisherDirectory, ViewTokenStore
from domain.html_inspection import inspect_html
from domain.publication import (ACTIVE, DISABLED, MAX_PROJECTS_PER_ARTIFACT,
                                is_published, is_suspended, within_project_limit)
from domain.view_token import generation_of, new_token, token_record

# 1つの共有アーティファクトが入れるプロジェクトの数。
# 閲覧ゲートは、開けるかを判じるときに先頭からこの数までしか見ない
# （読み取り回数が実行の予算に直結するため）。書き手がこれを超えて書くと、
# 投稿者には成功が返り、閲覧者だけが開けない状態になる。
# 数は infra/contract/token-records.json が正で、両側の検証がそこを見る。


class ManageError(Exception):
    """操作できない理由を、仕様のエラーコードとともに伝える。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ── 索引の読み書き ──────────────────────────────────────

def _meta_key(artifact_id: str) -> str:
    return f"meta/{artifact_id}.json"


def _read_meta(store: ArtifactStore, caller: Caller, artifact_id: str) -> dict:
    """扱ってよい索引を読む。扱えないものは見つからないものとして扱う。

    投稿者は自分が公開したもの、管理者は全員のものを扱える。
    """
    try:
        meta = json.loads(store.get(_meta_key(artifact_id)))
    except Exception as e:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。") from e

    if not caller.is_admin and meta.get("uploadedBy") != caller.id:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")
    return meta


def _write_meta(store: ArtifactStore, clock: Clock, meta: dict) -> None:
    meta["updatedAt"] = clock()
    store.put(_meta_key(meta["artifactId"]),
                   json.dumps(meta, ensure_ascii=False), "application/json")


def _viewer_url(viewer_domain: str, artifact_id: str) -> str:
    domain = viewer_domain or "{viewer-domain}"
    return f"https://{domain}/p/{artifact_id}/"


def _require_published(meta: dict) -> None:
    if not is_published(meta):
        raise ManageError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")


# ── 一覧 ────────────────────────────────────────────────

def list_artifacts(store: ArtifactStore, caller: Caller) -> dict:
    """扱えるものを新しい順に並べる。トークンは含めない。

    投稿者には自分が公開したものだけ、管理者には全員のものが並ぶ。
    誰が公開したかを添えるのは、管理者が引き継ぎ先を決めるのに要るため。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    一覧がすべて空になるのを避ける。黙って落とさないのは、投稿者が
    「公開したはずのものが消えた」と気づけないため（コメントの読み出しと
    同じ扱い）。
    """
    rows, unreadable = [], 0
    for key in store.list("meta/"):
        try:
            meta = json.loads(store.get(key))
        except Exception:
            unreadable += 1
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
            "comments": _count_comments(store, meta.get("artifactId", "")),
        })
    return {"artifacts": sorted(rows, key=lambda r: r["updatedAt"], reverse=True),
            "unreadable": unreadable}


def _count_comments(store: ArtifactStore, artifact_id: str) -> int:
    """反応の件数。差し替えの区切りは印であって反応ではないので数えない。

    一覧のたびに置き場を走査する。件数が増えると呼び出しも増えるが、
    管理APIは反応そのものへ書けないため、書き込みのたびに数を控えておく
    手立てが無い（数えるのはここだけ、という制約と引き換えの作り）。
    """
    if not artifact_id:
        return 0
    return sum(1 for key in store.list(f"comments/{artifact_id}/")
               if not key.endswith("-replaced.json"))


# ── 差し替え ────────────────────────────────────────────

def replace_content(store: ArtifactStore, clock: Clock, viewer_domain: str, caller: Caller, artifact_id: str, html: str) -> dict:
    """中身だけを入れ替える。URL・トークン・これまでの反応は保つ。

    入れ替えた時点を区切りとして反応の並びに残す。これより前の指摘が
    入れ替え前のものだと読み取れるようにするため。
    """
    meta = _read_meta(store, caller, artifact_id)
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
    now = clock()

    store.put(f"p/{artifact_id}/content.html", html, "text/html; charset=utf-8")

    # 差し替えの区切り。反応と同じ並びに載る1件の記録として残す
    store.put(
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
    _write_meta(store, clock, meta)
    _refresh_listings(store, meta)

    return {"artifactId": artifact_id, "url": _viewer_url(viewer_domain, artifact_id),
            "externalRefs": found["externalRefs"]}


# ── トークンの再発行 ────────────────────────────────────

def _generation(tokens: ViewTokenStore, artifact_id: str) -> int:
    """いま何代目か。読めなければ1代目として扱い、再発行そのものは止めない。"""
    try:
        record = tokens.get(f"token:{artifact_id}")
    except Exception:
        return 1
    return generation_of(record)


def _issue(tokens: ViewTokenStore, clock: Clock, artifact_id: str, generation: int) -> str:
    token = new_token()
    tokens.put(f"token:{artifact_id}",
                  token_record(token, clock(), generation=generation))
    return token


def reissue_token(store: ArtifactStore, tokens: ViewTokenStore, clock: Clock, viewer_domain: str, caller: Caller, artifact_id: str) -> dict:
    """新しいトークンを発行し、それまでのものを失効させる。URLは変えない。"""
    meta = _read_meta(store, caller, artifact_id)
    generation = _generation(tokens, artifact_id) + 1
    token = _issue(tokens, clock, artifact_id, generation)
    _write_meta(store, clock, meta)

    return {"artifactId": artifact_id, "token": token,
            "url": _viewer_url(viewer_domain, artifact_id), "generation": generation,
            "tokenShownOnce": True}


# ── 停止と再開 ──────────────────────────────────────────

def suspend(store: ArtifactStore, tokens: ViewTokenStore, clock: Clock, caller: Caller, artifact_id: str) -> dict:
    """公開を止める。中身も反応も消さない。"""
    meta = _read_meta(store, caller, artifact_id)
    _require_published(meta)

    tokens.put(f"token:{artifact_id}", "DISABLED")
    meta["status"] = DISABLED
    _write_meta(store, clock, meta)

    return {"artifactId": artifact_id, "status": DISABLED}


def resume(store: ArtifactStore, tokens: ViewTokenStore, clock: Clock, viewer_domain: str, caller: Caller, artifact_id: str) -> dict:
    """再び開けるようにする。トークンは必ず新しくなる。

    止める理由の多くは見せる相手を絞り直すことにあるため、止める前の
    トークンを復活させない。
    """
    meta = _read_meta(store, caller, artifact_id)
    if not is_suspended(meta):
        raise ManageError("NOT_SUSPENDED", "公開は止まっていません。")

    generation = _generation(tokens, artifact_id) + 1
    token = _issue(tokens, clock, artifact_id, generation)
    meta["status"] = ACTIVE
    _write_meta(store, clock, meta)

    return {"artifactId": artifact_id, "token": token,
            "url": _viewer_url(viewer_domain, artifact_id), "generation": generation,
            "status": ACTIVE, "tokenShownOnce": True}


# ── 引き継ぎ ────────────────────────────────────────────

def transfer(store: ArtifactStore, directory: PublisherDirectory, clock: Clock, caller: Caller, artifact_id: str, to_publisher: str) -> dict:
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

    meta = _read_meta(store, caller, artifact_id)

    if not (directory and directory.find(to_publisher)):
        # 招かれていない人へ移すと、その場で誰も手入れできない状態に戻る
        raise ManageError("PUBLISHER_NOT_FOUND", "移す先が招かれていません。")

    previous = meta.get("uploadedBy", "")
    meta["uploadedBy"] = to_publisher
    _write_meta(store, clock, meta)

    return {"artifactId": artifact_id, "from": previous, "to": to_publisher,
            "event": "ArtifactTransferred"}


# ── プロジェクトへの出し入れ ────────────────────────────

def _require_within_limit(projects: list[str]) -> None:
    """上限を超えていないかを、書き始める前に確かめる。"""
    if not within_project_limit(projects):
        raise ManageError(
            "TOO_MANY_PROJECTS",
            f"1つのアーティファクトが入れるプロジェクトは{MAX_PROJECTS_PER_ARTIFACT}件までです。"
            "どれかから外してから加えてください。")


def _write_membership(tokens: ViewTokenStore, artifact_id: str, projects: list[str]) -> None:
    """所属を、閲覧ゲートが読める形へ書き出す。

    上限を超えるものは書かずに拒む。黙って書くと、超えた分は閲覧ゲートから
    見えないまま所属したことになり、投稿者には成功が返って閲覧者だけが
    開けない。原因の分からない不具合になるため、ここで止める。
    """
    _require_within_limit(projects)     # 最後の守り。ここへ来る前に弾かれているはず
    tokens.put(f"pp:{artifact_id}", " ".join(projects))


def assign(store: ArtifactStore, tokens: ViewTokenStore, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """プロジェクトへ加える。人の明示的な操作でのみ成立する。

    加えられるのは自分が公開したものだけ。入れ先は、共有なら誰でも、
    個人なら持ち主だけ。この2つの判定を両方通ったときにだけ成立する。
    """
    import projects as project_store

    meta = _read_meta(store, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id and not caller.is_admin:
        # 他人のものを、勝手に誰かの見せる範囲へ入れられない
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = project_store.require_writable(store, caller, project_id)

    belongs = list(meta.get("projects") or [])
    if project_id not in belongs:               # 重ねて加えても二重にならない
        belongs.append(project_id)
    # 書き始める前に確かめる。索引を書いてから拒むと、索引と閲覧ゲート用の
    # 記録が食い違ったまま残る
    _require_within_limit(belongs)

    meta["projects"] = belongs
    _write_meta(store, clock, meta)
    _write_membership(tokens, artifact_id, belongs)
    _sync_project(store, clock, project_store, index, artifact_id, member=True)

    return {"artifactId": artifact_id, "projects": belongs}


def unassign(store: ArtifactStore, tokens: ViewTokenStore, clock: Clock, caller: Caller, artifact_id: str, project_id: str) -> dict:
    """プロジェクトから外す。共有アーティファクト自体は個別の閲覧トークンで開けるまま残る。"""
    import projects as project_store

    meta = _read_meta(store, caller, artifact_id)
    if meta.get("uploadedBy") != caller.id and not caller.is_admin:
        raise ManageError("ARTIFACT_NOT_FOUND", "見つかりません。")

    index = project_store.require_writable(store, caller, project_id)

    belongs = [p for p in (meta.get("projects") or []) if p != project_id]
    meta["projects"] = belongs
    _write_meta(store, clock, meta)
    _write_membership(tokens, artifact_id, belongs)
    _sync_project(store, clock, project_store, index, artifact_id, member=False)

    return {"artifactId": artifact_id, "projects": belongs}


def _sync_project(store: ArtifactStore, clock: Clock, project_store, index: dict, artifact_id: str, member: bool) -> None:
    """プロジェクトの索引と、閲覧者が見る一覧を揃える。

    所属は索引（人へ見せるための正）と pp:（閲覧ゲートが判じるための投影）の
    2か所に持つ。片方だけを書く経路を作らないため、出し入れのたびに
    ここを通す。
    """
    ids = [a for a in index.get("memberArtifactIds", []) if a != artifact_id]
    if member:
        ids.append(artifact_id)
    index["memberArtifactIds"] = ids
    index["updatedAt"] = clock()
    store.put(f"projects/{index['projectId']}.json",
                   json.dumps(index, ensure_ascii=False), "application/json")
    project_store.write_listing(store, index)


def _refresh_listings(store: ArtifactStore, meta: dict) -> None:
    """このアーティファクトが入っている全プロジェクトの一覧を書き直す。

    一覧は表示名を含むため、差し替えで名前が変わったときに書き直さないと、
    閲覧者へ古い名前が見え続ける。
    """
    import projects as project_store

    for project_id in meta.get("projects") or []:
        index = project_store.read_index(store, project_id)
        if index:
            project_store.write_listing(store, index)

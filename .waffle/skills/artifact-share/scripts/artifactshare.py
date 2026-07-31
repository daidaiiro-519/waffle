#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3", "awscrt"]
# ///
"""artifactshare.py — 手元から公開と管理を行うCLI。

既存の姉妹プロダクトのCLIから、配信に関わる部分だけを取り出したもの。
文書種別の選択肢の集合と、DESIGN.mdの確定にまつわる操作は持ち込まない
（親が子の事情を知る構造を作らないため）。

中身の検査は公開の受け口と同じ処理を使う。どちらから公開しても、外部への
参照の検出もメタ情報の読み取りも同じように効く。

使い方:
  artifactshare init                          環境を対話式に用意する
  artifactshare destroy                       環境を対話式に削除する（initの対）
  artifactshare list                          公開中・停止中の一覧
  artifactshare publish <html> [--name "表示名"] [--project <id>]
                                              公開して、URLとトークンを受け取る
  artifactshare replace <artifactId> <html>   中身だけを差し替える（URL・トークン・反応は保つ）
  artifactshare rotate <artifactId>           トークンを再発行する（URLは変わらない）
  artifactshare disable <artifactId>          公開を止める（データは残る）
  artifactshare enable <artifactId>           再び公開する（トークンは必ず新しくなる）
  artifactshare export <artifactId> [出力先]  中身と反応を手元へ取り出す
  artifactshare project <create|list|add|remove|rotate|disable>
                                              まとめて見せる単位を管理する
  artifactshare update-function               関門の実体を配信へ反映する
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambda" / "publish_artifact"))

# 検査・発行の処理は公開の受け口と共有する。経路が違っても同じ規則で扱うため
from main import (  # noqa: E402
    inspect_html,
    new_artifact_id,
    new_token,
    token_record,
)


class CliError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Env:
    """外部との接点。実物の組み立ては main() が行う。"""

    store: object          # put(key, body, content_type) / get(key) / list(prefix) / remove(key)
    keys: object           # put(key, value) / get(key)
    wrapper_template: str
    viewer_domain: str
    now: Callable[[], int]
    publisher: str


# ── 索引の読み書き ──────────────────────────────────────

def _meta_key(artifact_id: str) -> str:
    return f"meta/{artifact_id}.json"


def read_meta(env: Env, artifact_id: str) -> dict:
    try:
        return json.loads(env.store.get(_meta_key(artifact_id)))
    except Exception as e:
        raise CliError("ARTIFACT_NOT_FOUND", f"{artifact_id} が見つかりません。") from e


def write_meta(env: Env, meta: dict) -> None:
    meta["updatedAt"] = env.now()
    env.store.put(_meta_key(meta["artifactId"]),
                  json.dumps(meta, ensure_ascii=False), "application/json")


def _viewer_url(env: Env, artifact_id: str) -> str:
    return f"https://{env.viewer_domain}/p/{artifact_id}/"


def _require_published(meta: dict) -> None:
    if meta.get("status") != "active":
        raise CliError("NOT_PUBLISHED", "公開が止まっています。先に再公開してください。")


# ── 公開 ────────────────────────────────────────────────

def publish(env: Env, html: str, display_name: str | None, projects: list[str]) -> dict:
    """アップロードするHTMLを公開し、URLとトークンを返す。

    公開の受け口と同じく、トークンは最後に書く。それ以前で失敗したものは
    トークンが無いため誰にも開けない。
    """
    if not html or not html.strip():
        raise CliError("EMPTY_CONTENT", "中身が空です。")

    found = inspect_html(html)
    name = (display_name or "").strip() or found["title"]
    if not name:
        raise CliError("NAME_REQUIRED", "表示名を指定してください（--name）。")

    artifact_id = new_artifact_id()
    token = new_token()
    now = env.now()

    # アップロードするものは書き換えずにそのまま置く
    env.store.put(f"p/{artifact_id}/content.html", html, "text/html; charset=utf-8")

    viewer = env.wrapper_template.replace("{{アーティファクトID}}", artifact_id)
    viewer = viewer.replace("{{表示名}}", name)
    env.store.put(f"p/{artifact_id}/index.html", viewer, "text/html; charset=utf-8")

    write_meta(env, {
        "artifactId": artifact_id,
        "name": name,
        "status": "active",
        "projects": [],                      # 所属は下で明示的に加える
        "metaSource": "extracted" if found["detected"] else "manual",
        "docType": found["docType"],
        "documentId": found["documentId"],
        "description": found["description"],
        "tags": found["tags"],               # 目印として控えるだけ。所属には影響しない
        "uploadedBy": env.publisher,
        "externalRefs": found["externalRefs"],
        "publishedAt": now,
    })

    env.keys.put(f"token:{artifact_id}", token_record(token, now))

    for pid in projects:
        assign(env, artifact_id, pid)

    return {
        "artifactId": artifact_id,
        "token": token,                      # 返すのはこの一度きり
        "url": _viewer_url(env, artifact_id),
        "name": name,
        "externalRefs": found["externalRefs"],
    }


# ── 差し替え ────────────────────────────────────────────

def replace_content(env: Env, artifact_id: str, html: str) -> dict:
    """中身だけを入れ替える。URL・トークン・これまでの反応は保つ。

    入れ替えた時点を区切りとして反応の並びに残す。これより前の指摘が
    入れ替え前のものだと読み取れるようにするため。
    """
    if not html or not html.strip():
        raise CliError("EMPTY_CONTENT", "中身が空です。")

    meta = read_meta(env, artifact_id)
    _require_published(meta)

    found = inspect_html(html)
    now = env.now()

    env.store.put(f"p/{artifact_id}/content.html", html, "text/html; charset=utf-8")

    # 差し替えの区切り。反応と同じ並びに載る1件の記録として残す
    env.store.put(
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
    write_meta(env, meta)

    return {"artifactId": artifact_id, "url": _viewer_url(env, artifact_id),
            "externalRefs": found["externalRefs"]}


# ── トークンの再発行 ────────────────────────────────────

def _generation(env: Env, artifact_id: str) -> int:
    try:
        record = env.keys.get(f"token:{artifact_id}")
    except Exception:
        return 1
    if record == "DISABLED":
        return 1
    parts = record.split("|")
    return int(parts[2]) if len(parts) > 2 else 1


def reissue_token(env: Env, artifact_id: str, generation: int | None = None) -> dict:
    """新しいトークンを発行し、それまでのものを失効させる。URLは変えない。"""
    meta = read_meta(env, artifact_id)
    token = new_token()
    gen = generation if generation is not None else _generation(env, artifact_id) + 1

    env.keys.put(f"token:{artifact_id}", token_record(token, env.now(), generation=gen))
    write_meta(env, meta)

    return {"artifactId": artifact_id, "token": token,
            "url": _viewer_url(env, artifact_id), "generation": gen}


# ── 停止と再開 ──────────────────────────────────────────

def suspend(env: Env, artifact_id: str) -> dict:
    """公開を止める。中身も反応も消さない。"""
    meta = read_meta(env, artifact_id)
    _require_published(meta)

    env.keys.put(f"token:{artifact_id}", "DISABLED")
    meta["status"] = "disabled"
    write_meta(env, meta)

    return {"artifactId": artifact_id, "status": "disabled"}


def resume(env: Env, artifact_id: str) -> dict:
    """再び開けるようにする。トークンは必ず新しくなる。

    止める理由の多くが見せる相手を絞り直すことにあるため、止める前の
    トークンは復活させない。
    """
    meta = read_meta(env, artifact_id)
    if meta.get("status") != "disabled":
        raise CliError("NOT_SUSPENDED", "公開は止まっていません。")

    gen = _generation(env, artifact_id) + 1
    result = reissue_token(env, artifact_id, generation=gen)

    meta = read_meta(env, artifact_id)
    meta["status"] = "active"
    write_meta(env, meta)

    return {**result, "status": "active"}


# ── プロジェクトへの出し入れ ────────────────────────────

def _write_membership(env: Env, artifact_id: str, projects: list[str]) -> None:
    """所属を、関門が読める形へ書き出す。所属が無ければ記録も置かない。"""
    if projects:
        env.keys.put(f"pp:{artifact_id}", " ".join(projects))
    else:
        env.keys.put(f"pp:{artifact_id}", "")


def assign(env: Env, artifact_id: str, project_id: str) -> dict:
    """まとめて見せる単位へ加える。人の明示的な操作でのみ成立する。"""
    try:
        env.keys.get(f"proj:{project_id}")
    except Exception as e:
        raise CliError("PROJECT_NOT_FOUND", f"{project_id} が見つかりません。") from e

    meta = read_meta(env, artifact_id)
    projects = list(meta.get("projects") or [])
    if project_id not in projects:              # 重ねて加えても二重にならない
        projects.append(project_id)
    meta["projects"] = projects
    write_meta(env, meta)
    _write_membership(env, artifact_id, projects)

    return {"artifactId": artifact_id, "projects": projects}


def unassign(env: Env, artifact_id: str, project_id: str) -> dict:
    """まとめから外す。アーティファクト自体は個別のトークンで開けるまま残る。"""
    meta = read_meta(env, artifact_id)
    projects = [p for p in (meta.get("projects") or []) if p != project_id]
    meta["projects"] = projects
    write_meta(env, meta)
    _write_membership(env, artifact_id, projects)

    return {"artifactId": artifact_id, "projects": projects}


# ── 一覧 ────────────────────────────────────────────────

def list_artifacts(env: Env) -> list[dict]:
    """索引から一覧を組み立てる。トークンは含めない（取り出せてはならない）。"""
    rows = []
    for key in env.store.list("meta/"):
        try:
            meta = json.loads(env.store.get(key))
        except Exception:
            continue
        rows.append({
            "artifactId": meta.get("artifactId", ""),
            "name": meta.get("name", ""),
            "status": meta.get("status", ""),
            "docType": meta.get("docType", ""),
            "tags": meta.get("tags", []),
            "projects": meta.get("projects", []),
            "uploadedBy": meta.get("uploadedBy", ""),
            "updatedAt": meta.get("updatedAt", 0),
        })
    return sorted(rows, key=lambda r: r["updatedAt"], reverse=True)


# ── 受け口（実際の接続を組み立てる） ────────────────────

def _build_env() -> Env:  # pragma: no cover - 実際の接続を組み立てるだけ
    import os
    import time

    import boto3

    bucket = os.environ["CONTENT_BUCKET"]
    kvs_arn = os.environ["KVS_ARN"]
    s3 = boto3.client("s3")
    kvs = boto3.client("cloudfront-keyvaluestore")

    class _Store:
        def put(self, key, body, content_type):
            s3.put_object(Bucket=bucket, Key=key,
                          Body=body.encode("utf-8"), ContentType=content_type)

        def get(self, key):
            return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")

        def list(self, prefix):
            out, token = [], None
            while True:
                kw = {"Bucket": bucket, "Prefix": prefix}
                if token:
                    kw["ContinuationToken"] = token
                res = s3.list_objects_v2(**kw)
                out += [o["Key"] for o in res.get("Contents", [])]
                if not res.get("IsTruncated"):
                    return out
                token = res["NextContinuationToken"]

        def remove(self, key):
            s3.delete_object(Bucket=bucket, Key=key)

    class _Keys:
        def put(self, key, value):
            etag = kvs.describe_key_value_store(KvsARN=kvs_arn)["ETag"]
            kvs.put_key(KvsARN=kvs_arn, Key=key, Value=value, IfMatch=etag)

        def get(self, key):
            return kvs.get_key(KvsARN=kvs_arn, Key=key)["Value"]

    wrapper = (Path(__file__).resolve().parent.parent
               / "references" / "templates" / "share-wrapper.html")

    return Env(
        store=_Store(), keys=_Keys(),
        wrapper_template=wrapper.read_text(encoding="utf-8"),
        viewer_domain=os.environ.get("VIEWER_DOMAIN", ""),
        now=lambda: int(time.time()),
        publisher=os.environ.get("OPERATOR", "operator"),
    )


def main(argv: list[str]) -> int:  # pragma: no cover - 入出力の組み立て
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0

    cmd, rest = argv[0], argv[1:]
    env = _build_env()

    try:
        if cmd == "publish":
            if not rest:
                raise CliError("USAGE", "publish <html> [--name '表示名'] [--project <id>]")
            name = _option(rest, "--name")
            projects = _options(rest, "--project")
            html = Path(rest[0]).read_text(encoding="utf-8")
            r = publish(env, html, name, projects)
            print(f"\n公開しました: {r['name']}")
            print(f"  URL   : {r['url']}")
            print(f"  トークン: {r['token']}")
            if r["externalRefs"]:
                print(f"\n注意: 外部を{r['externalRefs']}件参照しています。"
                      "閲覧者の環境では読み込まれません。")
            print("\nトークンはこの一度しか表示されません。"
                  "URLとは別の手段で相手へ渡してください。")

        elif cmd == "replace":
            r = replace_content(env, rest[0], Path(rest[1]).read_text(encoding="utf-8"))
            print(f"差し替えました: {r['url']}（URL・トークン・反応は変わりません）")

        elif cmd == "rotate":
            r = reissue_token(env, rest[0])
            print(f"新しいトークン: {r['token']}\nURL: {r['url']}（変わりません）")
            print("それまでのトークンは使えなくなります。行き渡るまで少し時間がかかります。")

        elif cmd == "disable":
            suspend(env, rest[0])
            print("公開を止めました。データは残っており、あとから再公開できます。")

        elif cmd == "enable":
            r = resume(env, rest[0])
            print(f"再公開しました。新しいトークン: {r['token']}")

        elif cmd == "list":
            for row in list_artifacts(env):
                mark = "公開中" if row["status"] == "active" else "停止中"
                print(f"{row['artifactId']}  {mark}  {row['name']}")

        else:
            print(__doc__)
            return 2
    except CliError as e:
        print(f"error: {e.code}: {e.message}", file=sys.stderr)
        return 1
    return 0


def _option(argv: list[str], flag: str) -> str | None:  # pragma: no cover
    return argv[argv.index(flag) + 1] if flag in argv else None


def _options(argv: list[str], flag: str) -> list[str]:  # pragma: no cover
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag and i + 1 < len(argv)]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))

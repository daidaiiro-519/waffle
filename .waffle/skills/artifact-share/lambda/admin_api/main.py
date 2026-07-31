"""管理操作の受け口。

Cognitoで本人確認を通った投稿者が、ブラウザから呼ぶ唯一の入口。
公開も、その後の管理も、すべてここを通る。閲覧者はここへ来ない
（閲覧はトークンを見る関門だけで完結する）。

手元のCLIは環境の構築だけを担い、ここも保管も操作しない。管理操作を
CLIに持たせると、招かれた者だけが公開できるという前提が、AWSの権限を
持つ人の手元で成り立たなくなるため。

外部との接続を知っているのはこのファイルだけで、publish.py と manage.py は
渡されたものだけを使う。

対象の仕様: bc-artifact-share 配下のユースケース7件
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import manage
import publish

# 受け付ける操作と、それを担う処理。ここに無いものは受け付けない
ACTIONS = {
    "publish", "list", "replace", "rotate", "disable", "enable",
    "assign", "unassign",
}


def handler(event, context):  # pragma: no cover - 実際の接続を組み立てるだけ
    body = json.loads(event.get("body") or "{}")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    authorization = headers.get("authorization", "")

    action = body.get("action", "publish")
    if action not in ACTIONS:
        return _response(400, {"error": "UNKNOWN_ACTION", "message": "その操作はありません。"})

    publisher = _identify(authorization)
    if not publisher:
        return _response(403, {"error": "NOT_INVITED",
                               "message": "操作できるのは招かれた利用者だけです。"})

    try:
        if action == "publish":
            result = publish.publish({**body, "authorization": authorization},
                                     _publish_deps())
        else:
            result = _dispatch(action, manage.Deps(**_connections()), publisher, body)
        return _response(200, result)
    except publish.PublishError as e:
        return _response(403 if e.code == "NOT_INVITED" else 400,
                         {"error": e.code, "message": e.message})
    except manage.ManageError as e:
        return _response(404 if e.code == "ARTIFACT_NOT_FOUND" else 400,
                         {"error": e.code, "message": e.message})


def _dispatch(action, deps, publisher, body):  # pragma: no cover
    artifact_id = body.get("artifactId", "")
    if action == "list":
        return {"artifacts": manage.list_artifacts(deps, publisher)}
    if action == "replace":
        return manage.replace_content(deps, publisher, artifact_id, body.get("html", ""))
    if action == "rotate":
        return manage.reissue_token(deps, publisher, artifact_id)
    if action == "disable":
        return manage.suspend(deps, publisher, artifact_id)
    if action == "enable":
        return manage.resume(deps, publisher, artifact_id)
    if action == "assign":
        return manage.assign(deps, publisher, artifact_id, body.get("projectId", ""))
    return manage.unassign(deps, publisher, artifact_id, body.get("projectId", ""))


# ── 外部との接続 ────────────────────────────────────────

def _connections() -> dict:  # pragma: no cover
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
            keys, token = [], None
            while True:
                kw = {"Bucket": bucket, "Prefix": prefix}
                if token:
                    kw["ContinuationToken"] = token
                res = s3.list_objects_v2(**kw)
                keys += [o["Key"] for o in res.get("Contents", [])]
                if not res.get("IsTruncated"):
                    return keys
                token = res["NextContinuationToken"]

    class _Keys:
        def put(self, key, value):
            etag = kvs.describe_key_value_store(KvsARN=kvs_arn)["ETag"]
            kvs.put_key(KvsARN=kvs_arn, Key=key, Value=value, IfMatch=etag)

        def get(self, key):
            return kvs.get_key(KvsARN=kvs_arn, Key=key)["Value"]

    return {"store": _Store(), "keys": _Keys(),
            "viewer_domain": os.environ.get("VIEWER_DOMAIN", "")}


def _publish_deps() -> publish.Deps:  # pragma: no cover
    return publish.Deps(
        identify=_identify,
        wrapper_template=(Path(__file__).parent / "share-wrapper.html")
        .read_text(encoding="utf-8"),
        **_connections(),
    )


def _identify(authorization: str) -> str | None:  # pragma: no cover
    """利用者の証明を検証し、その人を表す値を返す。招かれていなければ None。"""
    from cognito import verify
    return verify(authorization, os.environ["USER_POOL_ID"],
                  os.environ["USER_POOL_CLIENT_ID"])


def _response(status: int, payload: dict) -> dict:  # pragma: no cover
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }

"""管理操作の管理API。

Cognitoで本人確認を通った投稿者が、ブラウザから呼ぶ唯一の入口。
公開も、その後の管理も、すべてここを通る。閲覧者はここへ来ない
（閲覧はトークンを見る閲覧ゲートだけで完結する）。

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

import comments as comment_store
import manage
import projects
import publish
import publishers

# 受け付ける操作。ここに無いものは受け付けない
ACTIONS = {
    "publish", "list", "replace", "rotate", "disable", "enable",
    "assign", "unassign", "transfer", "invite", "remove-publisher",
    "publishers", "resend-invite", "comments", "export",
    "projects", "project", "create-project", "reissue-project",
    "disable-project", "enable-project",
}

# 管理者のグループ名。Cognitoのトークンに含まれていれば管理者とみなす
ADMIN_GROUP = "administrators"


def handler(event, context):  # pragma: no cover - 実際の接続を組み立てるだけ
    body = json.loads(event.get("body") or "{}")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    authorization = headers.get("authorization", "")

    action = body.get("action", "publish")
    if action not in ACTIONS:
        return _response(400, {"error": "UNKNOWN_ACTION", "message": "その操作はありません。"})

    caller = _identify(authorization)
    if not caller:
        return _response(403, {"error": "NOT_INVITED",
                               "message": "操作できるのは招かれた利用者だけです。"})

    try:
        if action == "publish":
            result = publish.publish({**body, "authorization": authorization},
                                     _publish_deps())
        else:
            result = _dispatch(action, manage.Deps(**_connections()), caller, body)
        return _response(200, result)
    except publish.PublishError as e:
        return _response(403 if e.code == "NOT_INVITED" else 400,
                         {"error": e.code, "message": e.message})
    except projects.ProjectError as e:
        return _response(404 if e.code == "PROJECT_NOT_FOUND" else 400,
                         {"error": e.code, "message": e.message})
    except publishers.PublisherError as e:
        return _response(403 if e.code == "NOT_ADMINISTRATOR" else 400,
                         {"error": e.code, "message": e.message})
    except manage.ManageError as e:
        status = {"ARTIFACT_NOT_FOUND": 404,
                  "NOT_ADMINISTRATOR": 403,
                  "NOT_THE_PUBLISHER": 403}.get(e.code, 400)
        return _response(status, {"error": e.code, "message": e.message})


def _dispatch(action, deps, caller, body):  # pragma: no cover
    artifact_id = body.get("artifactId", "")
    if action == "list":
        return {"artifacts": manage.list_artifacts(deps, caller)}
    if action == "replace":
        return manage.replace_content(deps, caller, artifact_id, body.get("html", ""))
    if action == "rotate":
        return manage.reissue_token(deps, caller, artifact_id)
    if action == "disable":
        return manage.suspend(deps, caller, artifact_id)
    if action == "enable":
        return manage.resume(deps, caller, artifact_id)
    if action == "assign":
        return manage.assign(deps, caller, artifact_id, body.get("projectId", ""))
    if action == "unassign":
        return manage.unassign(deps, caller, artifact_id, body.get("projectId", ""))
    if action == "comments":
        return comment_store.read(deps, caller, artifact_id)
    if action == "export":
        return comment_store.export(deps, caller, artifact_id)
    if action == "transfer":
        return manage.transfer(deps, caller, artifact_id, body.get("toPublisher", ""))
    if action == "invite":
        return publishers.invite(deps, caller, body.get("email", ""))
    if action == "publishers":
        return {"publishers": publishers.list_publishers(deps, caller)}
    if action == "resend-invite":
        return publishers.resend_invite(deps, caller, body.get("publisherId", ""))

    project_id = body.get("projectId", "")
    if action == "projects":
        return {"projects": projects.list_projects(deps, caller)}
    if action == "project":
        return projects.detail(deps, caller, project_id)
    if action == "create-project":
        return projects.create(deps, caller, body.get("displayName", ""),
                               body.get("scope", ""), body.get("projectKey", ""))
    if action == "reissue-project":
        return projects.reissue_token(deps, caller, project_id)
    if action == "disable-project":
        return projects.suspend(deps, caller, project_id)
    if action == "enable-project":
        return projects.resume(deps, caller, project_id)
    return publishers.remove(deps, caller, body.get("publisherId", ""))


# ── 外部との接続 ────────────────────────────────────────

def _connections() -> dict:  # pragma: no cover
    import boto3

    bucket = os.environ["CONTENT_BUCKET"]
    kvs_arn = os.environ["KVS_ARN"]
    pool = os.environ["USER_POOL_ID"]
    s3 = boto3.client("s3")
    kvs = boto3.client("cloudfront-keyvaluestore")
    idp = boto3.client("cognito-idp")

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

    class _Directory:
        """招かれている人の名簿。実体は利用者プール。"""

        def find(self, publisher_id):
            try:
                got = idp.admin_get_user(UserPoolId=pool, Username=publisher_id)
            except Exception:
                return None
            # 仮の合言葉のまま入っていない人は、まだ招待に応じていない
            got["status"] = ("invited" if got.get("UserStatus") == "FORCE_CHANGE_PASSWORD"
                             else "active")
            return got

        def invite(self, email):
            """招いて、名簿が持つ識別子を返す。

            宛先で入る設定にしてあるため、名簿の識別子は宛先そのものではない。
            公開したものの持ち主はこの識別子で記録されるので、宛先を返すと
            招いた直後に引き継ぎ先として指せなくなる。
            """
            try:
                created = idp.admin_create_user(
                    UserPoolId=pool, Username=email,
                    UserAttributes=[{"Name": "email", "Value": email},
                                    {"Name": "email_verified", "Value": "true"}],
                    DesiredDeliveryMediums=["EMAIL"])
                return created["User"]["Username"]
            except idp.exceptions.UsernameExistsException:
                # 既に招かれている。合言葉も公開したものも変えない
                return idp.admin_get_user(UserPoolId=pool, Username=email)["Username"]

        def remove(self, publisher_id):
            idp.admin_delete_user(UserPoolId=pool, Username=publisher_id)

        def list(self):
            people, token = [], None
            while True:
                kw = {"UserPoolId": pool, "Limit": 60}
                if token:
                    kw["PaginationToken"] = token
                res = idp.list_users(**kw)
                for u in res.get("Users", []):
                    attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
                    people.append({
                        "id": u["Username"],
                        "email": attrs.get("email", ""),
                        # 仮の合言葉のまま入っていない人は、まだ招待に応じていない
                        "status": ("invited" if u.get("UserStatus") == "FORCE_CHANGE_PASSWORD"
                                   else "active"),
                    })
                token = res.get("PaginationToken")
                if not token:
                    return people

        def resend(self, publisher_id):
            person = self.find(publisher_id) or {}
            email = {a["Name"]: a["Value"]
                     for a in person.get("UserAttributes", [])}.get("email", publisher_id)
            idp.admin_create_user(
                UserPoolId=pool, Username=publisher_id,
                UserAttributes=[{"Name": "email", "Value": email},
                                {"Name": "email_verified", "Value": "true"}],
                MessageAction="RESEND",
                DesiredDeliveryMediums=["EMAIL"])

        def admins(self):
            res = idp.list_users_in_group(UserPoolId=pool,
                                          GroupName=ADMIN_GROUP, Limit=60)
            return {u["Username"] for u in res.get("Users", [])}

    return {"store": _Store(), "keys": _Keys(), "directory": _Directory(),
            "project_page": _read_template("project-page.html"),
            "viewer_domain": os.environ.get("VIEWER_DOMAIN", "")}


def _read_template(name: str) -> str:  # pragma: no cover
    """同梱した雛形を読む。管理APIの中に置いてある。"""
    try:
        return (Path(__file__).parent / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def _publish_deps() -> publish.Deps:  # pragma: no cover
    connections = _connections()
    connections.pop("directory")          # 公開は名簿を読まない
    connections.pop("project_page")       # 公開はプロジェクトの雛形を要らない
    return publish.Deps(
        identify=lambda auth: (_identify(auth) or manage.Caller("")).id or None,
        wrapper_template=(Path(__file__).parent / "share-wrapper.html")
        .read_text(encoding="utf-8"),
        **connections,
    )


def _identify(authorization: str) -> manage.Caller | None:  # pragma: no cover
    """利用者の証明を検証し、誰であるかと管理者かどうかを返す。

    招かれていなければ None。管理者かどうかは、証明に含まれるグループで決める
    （こちらで名簿を引き直さない。証明そのものが唯一の根拠であるため）。
    """
    from cognito import verify
    claims = verify(authorization, os.environ["USER_POOL_ID"],
                    os.environ["USER_POOL_CLIENT_ID"])
    if not claims:
        return None
    return manage.Caller(id=claims["username"],
                         is_admin=ADMIN_GROUP in claims.get("groups", []))


def _response(status: int, payload: dict) -> dict:  # pragma: no cover
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }

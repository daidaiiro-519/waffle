"""管理操作の管理API。

Cognitoで本人確認を通った投稿者が、ブラウザから呼ぶ唯一の入口。
公開も、その後の管理も、すべてここを通る。閲覧者はここへ来ない
（閲覧はトークンを見る閲覧ゲートだけで完結する）。

手元のCLIは環境の構築だけを担い、ここも保管も操作しない。管理操作を
CLIに持たせると、招かれた者だけが公開できるという前提が、AWSの権限を
持つ人の手元で成り立たなくなるため。

外部との接続を知っているのはこのファイルだけで、ユースケースは渡されたもの
だけを使う。ここは層のグラフの外にある合成ルートで、配線だけを持つ。

対象の仕様: bc-artifact-share 配下のユースケース
"""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

from adapters.outbound.cognito_publisher_directory import CognitoPublisherDirectory
from adapters.outbound.kvs_view_gate import KvsViewGate
from adapters.outbound.kvs_view_token_store import KvsViewTokenStore
from adapters.outbound.s3_artifact_store import S3ArtifactStore
from adapters.outbound.stored_comment_repository import StoredCommentRepository
from adapters.outbound.stored_project_repository import StoredProjectRepository
from adapters.outbound.stored_shared_artifact_repository import (
    StoredSharedArtifactRepository,
)
from adapters.outbound.stored_viewer_site import StoredViewerSite
from application.usecases.assign_artifact_to_project import AssignArtifactToProject
from application.usecases.browse_projects import BrowseProjects
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.create_project import CreateProject
from application.usecases.export_artifact import ExportArtifact
from application.usecases.invite_publisher import InvitePublisher
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.list_my_artifacts import ListMyArtifacts
from application.usecases.list_publishers import ListPublishers
from application.usecases.list_view_tokens import ListViewTokens
from application.usecases.publish_artifact import PublishArtifact
from application.usecases.read_comments import ReadComments
from application.usecases.replace_artifact_content import ReplaceArtifactContent
from application.usecases.resume_artifact import ResumeArtifact
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens
from application.usecases.revoke_view_token import RevokeViewToken
from application.usecases.suspend_artifact import SuspendArtifact
from application.usecases.transfer_artifact import TransferArtifact
from application.view_token_access import ViewTokenError
from domain.view_subject import ViewSubject
from shared.errors import ManageError, ProjectError, PublisherError


@dataclasses.dataclass
class Connections:
    """合成ルートが組み立てた結線の束。

    これは port ではない。port は能力ごとの型として ports.py にあり、各操作は
    自分が必要とする口だけを受け取る。ここは、その口の実物を1か所で組み立てて
    経路表へ配るための入れ物にすぎない。
    """

    store: object
    keys: object
    now: object
    viewer_domain: str = ""
    identify: object = None
    directory: object = None
    wrapper_template: str = ""
    project_page: str = ""

    @property
    def artifacts(self):
        """共有アーティファクトの読み書き。保管の上に載せて組み立てる。"""
        return StoredSharedArtifactRepository(self.store)

    @property
    def projects(self):
        """プロジェクトの読み書き。"""
        return StoredProjectRepository(self.store)

    @property
    def comments(self):
        """寄せられた反応の読み書き。"""
        return StoredCommentRepository(self.store)

    @property
    def gate(self):
        """閲覧の面が判じるための材料を渡す口。"""
        return KvsViewGate(self.keys)

    @property
    def viewer(self):
        """閲覧の面への配置と、そこへの案内。"""
        return StoredViewerSite(self.store, self.wrapper_template,
                                self.project_page, self.viewer_domain)


# 管理者のグループ名。Cognitoのトークンに含まれていれば管理者とみなす
ADMIN_GROUP = "administrators"


def handler(event, context):  # pragma: no cover - 実際の接続を組み立てるだけ
    body = json.loads(event.get("body") or "{}")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    # 証明は x-id-token で届く。authorization は配信の口が関数へ署名するのに
    # 使っており、そちらへ載せると署名の突き合わせが合わなくなる
    authorization = headers.get("x-id-token") or headers.get("authorization", "")

    action = body.get("action", "publish")
    if action not in ACTIONS:
        return _response(400, {"error": "UNKNOWN_ACTION", "message": "その操作はありません。"})

    caller = _identify(authorization)
    if not caller:
        return _response(403, {"error": "NOT_INVITED",
                               "message": "操作できるのは招かれた利用者だけです。"})

    try:
        if action == "publish":
            c = _publish_deps()
            result = PublishArtifact(c.artifacts, c.viewer, c.gate, c.identify, c.now).run(
                {**body, "authorization": authorization})
        else:
            result = _dispatch(action, Connections(**_connections()), caller, body)
        return _response(200, result)
    except PublishError as e:
        return _response(403 if e.code == "NOT_INVITED" else 400,
                         {"error": e.code, "message": e.message})
    except ProjectError as e:
        return _response(404 if e.code == "PROJECT_NOT_FOUND" else 400,
                         {"error": e.code, "message": e.message})
    except ViewTokenError as e:
        return _response(404 if e.code == "TARGET_NOT_FOUND" else 400,
                         {"error": e.code, "message": e.message})
    except PublisherError as e:
        return _response(403 if e.code == "NOT_ADMINISTRATOR" else 400,
                         {"error": e.code, "message": e.message})
    except ManageError as e:
        status = {"ARTIFACT_NOT_FOUND": 404,
                  "NOT_ADMINISTRATOR": 403,
                  "NOT_THE_PUBLISHER": 403}.get(e.code, 400)
        return _response(status, {"error": e.code, "message": e.message})


def _subject(body: dict):
    """要求が指している対象を読む。共有アーティファクトかプロジェクトのどちらか。"""
    if body.get("projectId"):
        return ViewSubject.project(body["projectId"])
    return ViewSubject.artifact(body.get("artifactId", ""))


# 操作の名前と、その行き先。
#
# 表にしてあるのは、どれにも当たらなかったときの行き先を持たせないため。
# 以前はここが連なった分岐で、最後の1つが名簿からの削除だった。操作を
# 1つ増やして行き先を書き忘れると、その操作は黙って削除を実行していた。
# 表であれば、行き先の無い操作は下で落ちる。
ROUTES = {
    "list":        lambda d, c, b: ListMyArtifacts(d.artifacts, d.comments).run(c),
    "replace":     lambda d, c, b: ReplaceArtifactContent(
        d.artifacts, d.projects, d.comments, d.viewer, d.now
    ).run(c, b.get("artifactId", ""), b.get("html", "")),
    "disable":     lambda d, c, b: SuspendArtifact(d.artifacts, d.gate, d.now).run(
        c, b.get("artifactId", "")),
    "enable":      lambda d, c, b: ResumeArtifact(d.artifacts, d.viewer, d.gate, d.now).run(
        c, b.get("artifactId", "")),
    "assign":      lambda d, c, b: _assign(d).run(
        "assign", c, b.get("artifactId", ""), b.get("projectId", "")),
    "unassign":    lambda d, c, b: _assign(d).run(
        "unassign", c, b.get("artifactId", ""), b.get("projectId", "")),
    "transfer":    lambda d, c, b: TransferArtifact(d.artifacts, d.directory, d.now).run(
        c, b.get("artifactId", ""), b.get("toPublisher", "")),

    "issue-token":       lambda d, c, b: IssueViewToken(
        d.artifacts, d.projects, d.gate, d.now
    ).run(c, _subject(b), b.get("name", ""), b.get("ttl")),
    "view-tokens":       lambda d, c, b: ListViewTokens(
        d.artifacts, d.projects, d.now).run(c, _subject(b)),
    "revoke-token":      lambda d, c, b: RevokeViewToken(
        d.artifacts, d.projects, d.gate, d.now).run(c, _subject(b), b.get("tokenId", "")),
    "revoke-all-tokens": lambda d, c, b: RevokeAllViewTokens(
        d.artifacts, d.projects, d.gate, d.now).run(c, _subject(b)),

    "comments":    lambda d, c, b: ReadComments(d.artifacts, d.comments).run(
        c, b.get("artifactId", "")),
    "export":      lambda d, c, b: ExportArtifact(d.artifacts, d.comments, d.viewer).run(
        c, b.get("artifactId", "")),

    "invite":           lambda d, c, b: _publishers(d).run("invite", c, email=b.get("email", "")),
    "resend-invite":    lambda d, c, b: _publishers(d).run(
        "resend", c, publisher_id=b.get("publisherId", "")),
    "remove-publisher": lambda d, c, b: _publishers(d).run(
        "remove", c, publisher_id=b.get("publisherId", "")),
    "publishers":       lambda d, c, b: {"publishers": ListPublishers(d.directory).run(c)},

    "projects":        lambda d, c, b: _browse(d).run("list", c),
    "project":         lambda d, c, b: _browse(d).run("detail", c, b.get("projectId", "")),
    "create-project":  lambda d, c, b: CreateProject(
        d.artifacts, d.projects, d.viewer, d.gate, d.now
    ).run(c, b.get("displayName", ""), b.get("scope", ""), b.get("projectKey", "")),
    "disable-project": lambda d, c, b: _project_access(d).run("suspend", c, b.get("projectId", "")),
    "enable-project":  lambda d, c, b: _project_access(d).run("resume", c, b.get("projectId", "")),
}


# 複数の操作を持つユースケースは、組み立てを1か所にまとめる。
# 同じ結線を行き先ごとに書くと、口を1つ足したときの直し漏れが出る
def _assign(d) -> AssignArtifactToProject:
    return AssignArtifactToProject(d.artifacts, d.projects, d.viewer, d.gate, d.now)


def _publishers(d) -> InvitePublisher:
    return InvitePublisher(d.artifacts, d.directory)


def _browse(d) -> BrowseProjects:
    return BrowseProjects(d.artifacts, d.projects, d.viewer)


def _project_access(d) -> ControlProjectAccess:
    return ControlProjectAccess(d.projects, d.viewer, d.gate, d.now)



# 受け付ける操作。ここに無いものは受け付けない。
# 表から導くのは、受け付ける操作と行き先を持つ操作を必ず一致させるため
ACTIONS = set(ROUTES) | {"publish"}


def _dispatch(action, deps, caller, body):
    route = ROUTES.get(action)
    if route is None:
        raise ManageError("UNKNOWN_ACTION", "その操作はありません。")
    return route(deps, caller, body)


# ── 外部との接続 ────────────────────────────────────────

def _connections() -> dict:  # pragma: no cover
    """口の実物を組み立てる。ここは配線だけで、実装は adapters が持つ。"""
    return {
        "store": S3ArtifactStore(os.environ["CONTENT_BUCKET"]),
        "keys": KvsViewTokenStore(os.environ["KVS_ARN"]),
        "directory": CognitoPublisherDirectory(os.environ["USER_POOL_ID"], ADMIN_GROUP),
        "project_page": _read_template("project-page.html"),
        "viewer_domain": os.environ.get("VIEWER_DOMAIN", ""),
    }


def _read_template(name: str) -> str:  # pragma: no cover
    """同梱した雛形を読む。管理APIの中に置いてある。"""
    try:
        return (Path(__file__).parent / name).read_text(encoding="utf-8")
    except OSError:
        return ""


def _publish_deps() -> Connections:  # pragma: no cover
    connections = _connections()
    connections.pop("directory")          # 公開は名簿を読まない
    connections.pop("project_page")       # 公開はプロジェクトの雛形を要らない
    return Connections(
        identify=lambda auth: (_identify(auth) or Caller("")).id or None,
        wrapper_template=(Path(__file__).parent / "share-wrapper.html")
        .read_text(encoding="utf-8"),
        **connections,
    )


def _identify(authorization: str) -> Caller | None:  # pragma: no cover
    """利用者の証明を検証し、誰であるかと管理者かどうかを返す。

    招かれていなければ None。管理者かどうかは、証明に含まれるグループで決める
    （こちらで名簿を引き直さない。証明そのものが唯一の根拠であるため）。
    """
    from cognito import verify
    claims = verify(authorization, os.environ["USER_POOL_ID"],
                    os.environ["USER_POOL_CLIENT_ID"])
    if not claims:
        return None
    return Caller(id=claims["username"],
                         is_admin=ADMIN_GROUP in claims.get("groups", []))


def _response(status: int, payload: dict) -> dict:  # pragma: no cover
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(payload, ensure_ascii=False),
    }

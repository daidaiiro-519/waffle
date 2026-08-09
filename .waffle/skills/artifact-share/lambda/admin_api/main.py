"""管理操作の管理APIの起動点。

Cognitoで本人確認を通った投稿者が、ブラウザから呼ぶ唯一の入口。公開も、その後の
管理も、すべてここを通る。閲覧者はここへ来ない（閲覧はトークンを見る閲覧ゲート
だけで完結する）。

手元のCLIは環境の構築だけを担い、ここも保管も操作しない。管理操作をCLIに
持たせると、招かれた者だけが公開できるという前提が、AWSの権限を持つ人の手元で
成り立たなくなるため。

ここは層のグラフの外にある合成ルート。外部との接続を知っているのはこのファイル
だけで、口の実物を組み立てて受け口へ渡すことに徹する。振り分けも、失敗を外の
言葉へ写すことも、受け口（adapters/inbound）が担う。
"""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path

from adapters.inbound.admin_api import ACTIONS, dispatch, status_of
from adapters.outbound.cognito_publisher_directory import CognitoPublisherDirectory
from adapters.outbound.kvs_view_gate import KvsViewGate
from adapters.outbound.kvs_view_token_store import KvsViewTokenStore
from adapters.outbound.random_identifier import RandomIdGenerator
from adapters.outbound.s3_artifact_store import S3ArtifactStore
from adapters.outbound.stored_comment_repository import StoredCommentRepository
from adapters.outbound.stored_project_repository import StoredProjectRepository
from adapters.outbound.stored_shared_artifact_repository import (
    StoredSharedArtifactRepository,
)
from adapters.outbound.stored_viewer_site import StoredViewerSite
from application.ports import Caller
from application.usecases.publish_artifact import PublishArtifact
from shared.errors import ApplicationError

ADMIN_GROUP = os.environ.get("ADMIN_GROUP", "administrators")


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
    ids: object = dataclasses.field(default_factory=RandomIdGenerator)

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
    """入ってきた要求を受け取り、受け口へ渡して応答を返す。

    Args:
        event: 受け取った要求そのもの。
        context: 実行環境が添える情報。この処理では使わない。

    Returns:
        外の言葉へ直した応答。

    Raises:
        なし。失敗は応答の形で返す。
    """
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
            result = PublishArtifact(c.artifacts, c.viewer, c.gate, c.identify, c.now, c.ids).run(
                {**body, "authorization": authorization})
        else:
            result = dispatch(action, Connections(**_connections()), caller, body)
        return _response(200, result)
    except ApplicationError as e:
        return _response(status_of(e), {"error": e.code, "message": e.message})


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
    from adapters.outbound.cognito import verify
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

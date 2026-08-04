"""公開。

アップロードされたHTMLを受け取り、閲覧できる状態にして、URLとトークンを返す。
利用者の確認・中身の検査・artifactIdとトークンの発行・配置を担う。公開の経路は
これひとつだけで、中身の検査を経ずに保管へ書き込む手段は用意しない。

外部への接続は依存として受け取る。実際の接続を組み立てるのは main.py だけで、
ここは渡されたものだけを使う。検証のときは偽の依存を渡せる。

対象の仕様: uc-publish-artifact / agg-shared-artifact
"""

from __future__ import annotations

import json

from domain.html_inspection import inspect_html
from domain.identifier import new_artifact_id
from domain.publication import MAX_CONTENT_BYTES
from domain.artifact_content import fingerprint as content_fingerprint
from domain.view_subject import ViewSubject

# 公開したときに最初に発行される1本の名前。あとから名前を付けて増やせる
FIRST_TOKEN_NAME = "最初の共有"
from domain import view_token
from shared.errors import PublishError
from application.ports import Clock, PublisherIdentifier
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.viewer_site import ViewerSitePort
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.shared_artifact_repository import SharedArtifactRepository
import time
from dataclasses import dataclass
from typing import Callable



# ── 公開 ────────────────────────────────────────────────

def publish(artifacts: SharedArtifactRepository, viewer: ViewerSitePort, gate: ViewGatePort, identify: PublisherIdentifier, clock: Clock, request: dict) -> dict:
    """アップロードされたHTMLを公開し、URLとトークンを返す。

    途中で失敗したときに開ける状態のものを残さないことを、書き込む順序で保証する。
    トークンを最後に書くため、それ以前で失敗すると、置かれたファイルは残るものの
    トークンが存在せず、閲覧ゲートがすべての要求を拒む（誰も開けない）。

    置いたものを消して回る作りにはしない。この管理APIには削除の権限を与えておらず、
    与えると、破られたときの被害が反応や記録にまで及ぶため。到達できないまま
    残ったファイルの片付けは、権限を持つ責任者の運用として行う。
    """
    publisher = identify(request.get("authorization", ""))
    if not publisher:
        raise PublishError("NOT_INVITED", "公開できるのは招かれた利用者だけです。")

    content = request.get("html", "")
    if not content or not content.strip():
        raise PublishError("EMPTY_CONTENT", "中身が空です。")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        raise PublishError("CONTENT_TOO_LARGE", "受け取れる大きさを超えています。")

    found = inspect_html(content)
    display_name = (request.get("displayName") or "").strip()

    if found["detected"]:
        title = found["title"] or display_name
        meta_source = "extracted"
    else:
        title = display_name or found["title"]
        meta_source = "manual"
        if not display_name:
            # 題名だけを尋ねる。ここで尋ねる項目を増やさない
            raise PublishError("NAME_REQUIRED", "表示名を入力してください。")

    artifact_id = new_artifact_id()
    token = view_token.new_token()
    now = clock()
    first = view_token.issued(view_token.new_token_id(), FIRST_TOKEN_NAME,
                              gate.fingerprint_of(token),
                              view_token.expires_at(now), now)

    try:
        page_version = viewer.place_artifact(artifact_id, content, title)

        record = {
            "artifactId": artifact_id,
            "name": title,
            "status": "active",
            "projects": [],
            "metaSource": meta_source,
            "docType": found["docType"],
            "documentId": found["documentId"],
            "description": found["description"],
            "tags": found["tags"],
            "uploadedBy": publisher,
            "externalRefs": found["externalRefs"],
            "contentHash": content_fingerprint(content),
            "wrapperHash": page_version,
            "publishedAt": now,
            "updatedAt": now,
            "viewTokens": [first],
        }
        artifacts.save(record)

        # 閲覧の面へ渡すのは最後。ここまで成功して初めて開ける状態になる
        gate.replace_grants(ViewSubject.artifact(artifact_id),
                            view_token.grants([first], now))
    except PublishError:
        raise
    except Exception as e:
        # トークンを書く前に失敗しているため、置かれたものは誰にも開けない
        raise PublishError("PUBLISH_FAILED", f"公開できませんでした: {e}") from e

    return {
        "artifactId": artifact_id,
        "token": token,               # 返すのはこの一度きり。保管には残さない
        "url": viewer.artifact_url(artifact_id),
        "descriptor": {
            "documentId": found["documentId"],
            "docType": found["docType"],
            "title": title,
            "description": found["description"],
            "tags": found["tags"],
        },
        "metaSource": meta_source,
        "externalRefs": found["externalRefs"],
        "needsName": False,
        "tokenShownOnce": True,       # 呼び出し側へ、二度は示せないことを伝える
    }

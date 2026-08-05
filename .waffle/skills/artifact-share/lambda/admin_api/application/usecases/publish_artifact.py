"""手元の文書を、渡した相手に見てもらえる状態にする。

利用者の確認・中身の検査・識別子と閲覧トークンの発行・配置を担う。公開の経路は
これひとつだけで、中身の検査を経ずに保管へ書き込む手段は用意しない。

閲覧の面へ渡すのは最後。そこまで成功して初めて開ける状態になるので、途中で
失敗しても誰にも開けないものが残るだけで済む。

対象の仕様: uc-publish-artifact
"""
from __future__ import annotations

from dataclasses import dataclass

from application.ports import Clock, PublisherIdentifier
from application.ports.shared_artifact_repository import SharedArtifactRepository
from application.ports.view_gate import ViewGatePort
from application.ports.viewer_site import ViewerSitePort
from domain import view_token
from domain.artifact_content import fingerprint as content_fingerprint
from domain.html_inspection import inspect_html
from domain.identifier import new_artifact_id
from domain.shared_artifact import EXTRACTED, MANUAL
from domain.shared_artifact import (ArtifactDescriptor, ArtifactId, ArtifactStatus,
                                    MAX_CONTENT_BYTES,
                                    PUBLISHED, PublisherId, SharedArtifact)
from domain.view_subject import ViewSubject
from shared.errors import PublishError

FIRST_TOKEN_NAME = "最初の共有"



@dataclass(frozen=True)
class PublishedDescriptor:
    """公開したものに添えられた、控えるべき情報。"""

    document_id: str
    doc_type: str
    title: str
    description: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class PublishedArtifact:
    """公開した結果。閲覧トークンはこの一度きり示され、以後は見返せない。"""

    artifact_id: str
    token: str
    url: str
    descriptor: PublishedDescriptor
    meta_source: str
    external_refs: int
    needs_name: bool = False
    token_shown_once: bool = True

def _publish(artifacts: SharedArtifactRepository, viewer: ViewerSitePort, gate: ViewGatePort, identify: PublisherIdentifier, clock: Clock, request: dict) -> PublishedArtifact:
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
        meta_source = EXTRACTED
    else:
        title = display_name or found["title"]
        meta_source = MANUAL
        if not display_name:
            # 題名だけを尋ねる。ここで尋ねる項目を増やさない
            raise PublishError("NAME_REQUIRED", "表示名を入力してください。")

    artifact_id = new_artifact_id()
    token = view_token.new_token()
    now = clock()
    first = view_token.issued(FIRST_TOKEN_NAME, gate.fingerprint_of(token),
                              view_token.expires_at(now), now)

    try:
        viewer.place_artifact(artifact_id, content, title)

        artifacts.save(SharedArtifact(
            artifact_id=ArtifactId(artifact_id),
            display_name=title,
            content_fingerprint=content_fingerprint(content),
            view_tokens=(first,),
            status=ArtifactStatus(PUBLISHED),
            published_by=PublisherId(publisher),
            descriptor=ArtifactDescriptor(
                document_id=found["documentId"],
                doc_type=found["docType"],
                title=title,
                description=found["description"],
                labels=tuple(found["tags"]),
                source=meta_source,
            ),
            published_at=now,
            updated_at=now,
            external_resource_count=found["externalRefs"],
        ))

        # 閲覧の面へ渡すのは最後。ここまで成功して初めて開ける状態になる
        gate.replace_grants(ViewSubject.artifact(artifact_id),
                            view_token.grants((first,), now))
    except PublishError:
        raise
    except Exception as e:
        # トークンを書く前に失敗しているため、置かれたものは誰にも開けない
        raise PublishError("PUBLISH_FAILED", f"公開できませんでした: {e}") from e

    return PublishedArtifact(
        artifact_id=artifact_id,
        token=token,                  # 返すのはこの一度きり。保管には残さない
        url=viewer.artifact_url(artifact_id),
        descriptor=PublishedDescriptor(
            document_id=found["documentId"],
            doc_type=found["docType"],
            title=title,
            description=found["description"],
            tags=tuple(found["tags"]),
        ),
        meta_source=meta_source,
        external_refs=found["externalRefs"],
    )


class PublishArtifact:
    """手元の文書を、渡した相手に見てもらえる状態にする。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, viewer: ViewerSitePort, gate: ViewGatePort, identify: PublisherIdentifier, clock: Clock) -> None:
        self._artifacts = artifacts
        self._viewer = viewer
        self._gate = gate
        self._identify = identify
        self._clock = clock

    def run(self, request: dict) -> PublishedArtifact:
        """このユースケースの唯一の入口。"""
        return _publish(self._artifacts, self._viewer, self._gate, self._identify, self._clock, request)

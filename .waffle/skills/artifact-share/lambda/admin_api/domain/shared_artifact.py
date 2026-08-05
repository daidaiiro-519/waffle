"""共有アーティファクト。

渡した相手に見てもらうために公開された文書1件と、それを開くための閲覧トークン
の束をひとまとまりとして扱う。この2つを一緒に持つのは、閲覧トークンの本数や
名前の重なりを判じるのに、束を丸ごと見る必要があるため。

中身そのものはこの境界の外にある。どの不変条件も中身を読まないので、指紋だけを
持つ。中身は識別子で指して別の口から読み書きする。

状態は外から直接書き換えられない。変えたいときは、変えた結果を持つ新しい共有
アーティファクトを受け取る。不変条件を守る道をメソッドに限らないと、その道を
迂回する代入が残る。

対象の仕様: agg-shared-artifact
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from domain.view_token import ArtifactViewToken

# 公開されているかどうか
PUBLISHED = "PUBLISHED"
SUSPENDED = "SUSPENDED"

# 1つの共有アーティファクトが同時に入れるプロジェクトの数
MAX_PROJECTS = 3

# 目印の出どころ
EXTRACTED = "extracted"   # 中身から取り出した
MANUAL = "manual"         # 人が与えた


@dataclass(frozen=True)
class ArtifactId:
    """公開された共有アーティファクトを一意に指す短いID。"""

    value: str


@dataclass(frozen=True)
class PublisherId:
    """公開した人を指す識別子。招かれた者にのみ与えられる。"""

    value: str


@dataclass(frozen=True)
class ArtifactStatus:
    """公開されているかどうか。PUBLISHED と SUSPENDED のいずれか。"""

    value: str

    def is_published(self) -> bool:
        return self.value == PUBLISHED

    def is_suspended(self) -> bool:
        return self.value == SUSPENDED


@dataclass(frozen=True)
class ArtifactDescriptor:
    """共有アーティファクトに添えられた識別子・種別・題名・要約・分類の目印。

    中身に書かれていれば取り出し、書かれていなければ題名だけを人が与える。
    種別と分類の目印は保持するだけで、値の意味を解釈しない——解釈すると、
    中身に書ける値が誰に見せるかを左右してしまう。
    """

    document_id: str = ""
    doc_type: str = ""
    title: str = ""
    description: str = ""
    labels: tuple[str, ...] = ()
    source: str = MANUAL


@dataclass(frozen=True)
class SharedArtifact:
    """公開された文書1件。"""

    artifact_id: ArtifactId
    display_name: str
    content_fingerprint: str
    view_tokens: tuple[ArtifactViewToken, ...]
    status: ArtifactStatus
    published_by: PublisherId
    descriptor: ArtifactDescriptor
    published_at: int
    updated_at: int
    projects: tuple[str, ...] = ()
    external_resource_count: int = 0

    # ── 誰が手入れしてよいか ──────────────────────────

    def manageable_by(self, caller_id: str, is_admin: bool = False) -> bool:
        """その人が手入れしてよいか。公開した本人か、管理者であること。

        扱えないものを「拒む」ではなく「見つからない」として扱う決まりだが、
        その言い換えはここではしない。誰に向けて何と答えるかは呼び出し側が決める。
        """
        return is_admin or self.published_by.value == caller_id

    # ── 状態を変える ──────────────────────────────────

    def suspended(self, at: int) -> "SharedArtifact":
        """見せるのを止める。中身も反応も消さない。"""
        return replace(self, status=ArtifactStatus(SUSPENDED), updated_at=at)

    def resumed(self, at: int) -> "SharedArtifact":
        """もう一度見てもらえる状態に戻す。閲覧トークンはそのまま。"""
        return replace(self, status=ArtifactStatus(PUBLISHED), updated_at=at)

    def with_content(self, fingerprint: str, descriptor: ArtifactDescriptor,
                     external_resource_count: int, at: int) -> "SharedArtifact":
        """中身を丸ごと差し替える。共有URLも閲覧トークンも変えない。"""
        return replace(self, content_fingerprint=fingerprint, descriptor=descriptor,
                       external_resource_count=external_resource_count, updated_at=at)

    def transferred_to(self, publisher: PublisherId, at: int) -> "SharedArtifact":
        """手入れできる人を替える。渡した相手の手元では何も変わらない。"""
        return replace(self, published_by=publisher, updated_at=at)

    def with_view_tokens(self, tokens: tuple[ArtifactViewToken, ...],
                         at: int) -> "SharedArtifact":
        """閲覧トークンの顔ぶれを置き換える。"""
        return replace(self, view_tokens=tuple(tokens), updated_at=at)

    # ── プロジェクトへの出し入れ ──────────────────────

    def can_join(self, project_id: str) -> bool:
        """これ以上プロジェクトへ入れるか。既に入っているものは数に含めない。"""
        return project_id in self.projects or len(self.projects) < MAX_PROJECTS

    def joined(self, project_id: str, at: int) -> "SharedArtifact":
        """プロジェクトへ加える。既に入っていれば何も変わらない。"""
        if project_id in self.projects:
            return self
        return replace(self, projects=self.projects + (project_id,), updated_at=at)

    def left(self, project_id: str, at: int) -> "SharedArtifact":
        """プロジェクトから外す。共有アーティファクト自体は失われない。"""
        return replace(self, projects=tuple(p for p in self.projects if p != project_id),
                       updated_at=at)

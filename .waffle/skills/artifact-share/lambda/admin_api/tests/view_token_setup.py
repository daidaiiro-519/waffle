"""閲覧トークンのテストが共有する結線と偽実装。

偽実装をテストごとに作ると少しずつ食い違い、実物なら失敗する場面で緑になる。
1か所に置いて、閲覧トークンに関わるすべてのテストがここを使う。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from usecase_builder import build  # noqa: E402
from application.usecases.issue_view_token import IssueViewToken  # noqa: E402
from application.usecases.list_view_tokens import ListViewTokens  # noqa: E402
from application.usecases.revoke_all_view_tokens import RevokeAllViewTokens  # noqa: E402
from application.usecases.revoke_view_token import RevokeViewToken  # noqa: E402

from application.view_token_access import ViewTokenError  # noqa: E402

from adapters.outbound.kvs_view_gate import KvsViewGate  # noqa: E402
from application.ports import Caller  # noqa: E402
from domain import view_token  # noqa: E402
from domain.project import (  # noqa: E402
    PUBLISHED as PROJECT_PUBLISHED, Project, ProjectId, ProjectKey,
    ProjectOwner, ProjectScope, ProjectStatus, SHARED,
)
from domain.shared_artifact import (  # noqa: E402
    ArtifactDescriptor, ArtifactId, ArtifactStatus, PUBLISHED,
    PublisherId, SharedArtifact,
)
from domain.view_subject import ViewSubject  # noqa: E402

ME = Caller("publisher-1")
OTHER = Caller("publisher-2")
ADMIN = Caller("admin-1", is_admin=True)

NOW = 1_700_000_000
AID = "aaaaaaaa"
PID = "p7k2xq"


class FakeKeys:
    def __init__(self):
        self.written = {}

    def put(self, key, value):
        self.written[key] = value

    def get(self, key):
        return self.written[key]


class FakeRepo:
    """識別子で引ける置き場所。共有アーティファクトにもプロジェクトにも使う。

    保管の形ではなく集約そのものを持つ。ここで確かめたいのは操作の振る舞いで
    あって、保管との翻訳ではない（翻訳は test_repository_translation が見る）。
    """

    def __init__(self, records=None):
        self.records = dict(records or {})

    def find(self, key):
        return self.records.get(key)

    def save(self, aggregate):
        key = getattr(aggregate, "artifact_id", None) or aggregate.project_id
        self.records[key.value] = aggregate

    def all(self):
        return list(self.records.values()), 0


class Wiring:
    """検証のための結線の束。合成ルートが持つのと同じ名前で口を持つ。"""

    def __init__(self, artifacts, projects, gate, at=None):
        self.artifacts, self.projects, self.gate = artifacts, projects, gate
        self.comments = self.viewer = self.directory = self.identify = None
        self.now = (lambda: at) if at is not None else (lambda: NOW)

    def at(self, when):
        """時計だけを進めた同じ結線。"""
        return Wiring(self.artifacts, self.projects, self.gate, at=when)


def setup(tokens=None, owner="publisher-1"):
    """公開済みのものが1件あり、プロジェクトも1つある状態を作る。"""
    artifacts = FakeRepo({AID: SharedArtifact(
        artifact_id=ArtifactId(AID), display_name="設計レビュー", content_fingerprint="",
        view_tokens=tuple(tokens or ()), status=ArtifactStatus(PUBLISHED),
        published_by=PublisherId(owner), descriptor=ArtifactDescriptor(),
        published_at=NOW, updated_at=NOW)})
    projects = FakeRepo({PID: Project(
        project_id=ProjectId(PID), display_name="まとめ", project_key=ProjectKey(),
        status=ProjectStatus(PROJECT_PUBLISHED), owner=ProjectOwner(owner),
        scope=ProjectScope(SHARED), created_at=NOW,
        view_tokens=tuple(tokens or ()), updated_at=NOW)})
    gate = KvsViewGate(FakeKeys())
    return Wiring(artifacts, projects, gate)


def issue(deps, name, ttl=None, caller=ME, subject=None, at=NOW):
    return build(deps.at(at), IssueViewToken).run(
        caller, subject or ViewSubject.artifact(AID), name, ttl)

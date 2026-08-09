"""集約の読み書きの口が守る約束を、本物と偽物の両方に対して確かめる。

実行:  python3 -m pytest tests/ -v

同じ問いを2つの実装へ投げる。偽物が本物より甘くなると、実物なら失敗する場面で
検証だけが緑になる。この文脈では、その形の事故が既に一度起きている——偽物が
公開の検証と管理の検証で別々に育ち、片方だけが失敗を作れる状態になっていた。

本物を実物の保管へ繋がずに動かせるのは、保管を渡して受け取る形になっているため。
名簿の口は本物が利用者プールへ直接つながるので、ここでは扱わない（規約が実物の
サービスに依存する単体の検証を禁じている）。

対象の仕様: agg-shared-artifact / agg-project（集約の読み書きの口）
"""
import pytest

from adapters.outbound.stored_project_repository import StoredProjectRepository
from adapters.outbound.stored_shared_artifact_repository import (
    StoredSharedArtifactRepository,
)
from domain.entities.project import Project
from domain.entities.shared_artifact import SharedArtifact
from domain.value_objects.artifact_content import ContentFingerprint
from domain.value_objects.project import (
    PUBLISHED as PROJECT_PUBLISHED, ProjectId, ProjectKey, ProjectOwner, ProjectScope,
    ProjectStatus,
)
from domain.value_objects.shared_artifact import (
    PUBLISHED, ArtifactDescriptor, ArtifactId, ArtifactStatus, PublisherId,
)
from fakes import FakeStore
from view_token_setup import FakeRepo

AID = "aaaaaaaa"
PID = "p7k2xq"
NOW = 1_700_000_000


def _artifact(artifact_id=AID, owner="publisher-1"):
    return SharedArtifact(
        artifact_id=ArtifactId(artifact_id), display_name="設計レビュー",
        content_fingerprint=ContentFingerprint("abc"), view_tokens=(),
        status=ArtifactStatus(PUBLISHED), published_by=PublisherId(owner),
        descriptor=ArtifactDescriptor(), published_at=NOW, updated_at=NOW)


def _project(project_id=PID, owner="publisher-1"):
    return Project(
        project_id=ProjectId(project_id), display_name="まとめ",
        project_key=ProjectKey(), status=ProjectStatus(PROJECT_PUBLISHED),
        owner=ProjectOwner(owner), scope=ProjectScope("SHARED"), created_at=NOW)


# 同じ問いを投げる相手。本物は保管を渡して組み立て、偽物はそのまま使う
ARTIFACT_REPOS = [
    pytest.param(lambda: StoredSharedArtifactRepository(FakeStore()), id="本物"),
    pytest.param(FakeRepo, id="偽物"),
]
PROJECT_REPOS = [
    pytest.param(lambda: StoredProjectRepository(FakeStore()), id="本物"),
    pytest.param(FakeRepo, id="偽物"),
]


@pytest.mark.parametrize("make", ARTIFACT_REPOS)
def test_無いものを引くと見つからないと答える(make):
    """例外ではなく、見つからないという答えを返す。呼び出し側はそれで分岐する。"""
    assert make().find("zzzzzzzz") is None


@pytest.mark.parametrize("make", ARTIFACT_REPOS)
def test_残したものが同じ識別子で引ける(make):
    repo = make()
    repo.save(_artifact())

    found = repo.find(AID)

    assert found is not None
    assert found.artifact_id.value == AID


@pytest.mark.parametrize("make", ARTIFACT_REPOS)
def test_残し直すと置き換わり増えない(make):
    """同じ識別子で2度残しても2件にならない。"""
    repo = make()
    repo.save(_artifact())
    repo.save(_artifact())

    found, _ = repo.all()

    assert len(found) == 1


@pytest.mark.parametrize("make", ARTIFACT_REPOS)
def test_全て取り出すと一覧と読めなかった件数が返る(make):
    """読めなかったものを黙って落とさない。件数を必ず添える。"""
    repo = make()
    repo.save(_artifact())

    found, unreadable = repo.all()

    assert [a.artifact_id.value for a in found] == [AID]
    assert unreadable == 0


@pytest.mark.parametrize("make", ARTIFACT_REPOS)
def test_何も無ければ空の一覧が返る(make):
    found, unreadable = make().all()

    assert found == []
    assert unreadable == 0


@pytest.mark.parametrize("make", PROJECT_REPOS)
def test_プロジェクトも同じ約束を守る(make):
    repo = make()
    assert repo.find("zzzzzz") is None

    repo.save(_project())

    assert repo.find(PID).project_id.value == PID
    found, unreadable = repo.all()
    assert len(found) == 1 and unreadable == 0

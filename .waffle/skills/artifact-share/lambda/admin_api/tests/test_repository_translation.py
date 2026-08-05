"""保管の記録と集約の型を結ぶ翻訳を、手で置いた記録から確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

保管に残っている欄名（name / uploadedBy / contentHash）と、宣言された業務の語
（displayName / publishedBy / contentFingerprint）は別である。両者を結ぶのは
repository だけで、そこが唯一この対応を知る。

ここに置く記録は、実装から生成していない。実際に保管へ残っている形をそのまま
手で書いた——生成すると、翻訳表の写しが1つ増えるだけで突き合わせにならない。

2026-08-01に、これと同じ構図で事故が起きている。閲覧の面へ渡す記録の形が
ずれたまま、実装も検証も同じ誤解で書かれており、137件すべて緑のまま実環境で
だけ現れた。翻訳表を実装より先に固定するのは、その再発を止めるため。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.outbound.stored_project_repository import (  # noqa: E402
    from_record as project_from_record,
    to_record as project_to_record,
)
from adapters.outbound.stored_shared_artifact_repository import (  # noqa: E402
    from_record as artifact_from_record,
    to_record as artifact_to_record,
)
from domain.project import PUBLISHED as PROJECT_PUBLISHED  # noqa: E402
from domain.shared_artifact import EXTRACTED, PUBLISHED, SUSPENDED  # noqa: E402
from domain.view_token import ACTIVE  # noqa: E402

# いま保管に残っている形。欄名も値も、実物のとおりに書く
共有アーティファクトの記録 = {
    "artifactId": "aaaaaaaa",
    "name": "検索基盤にPostgreSQLを採用する",
    "status": "active",
    "projects": ["p7k2xq"],
    "metaSource": "extracted",
    "docType": "DecisionRecord",
    "documentId": "adr-search-backend",
    "description": "新規ミドルウェアを入れず既存DBの拡張で実装する判断",
    "tags": ["backend", "search"],
    "uploadedBy": "publisher-1",
    "externalRefs": 3,
    "contentHash": "c4a7c5c66b583eb3a49cb973802390c3",
    "wrapperHash": "7a81f0974b8a6270b3b0fe1214143ca0",
    "publishedAt": 1_700_000_000,
    "updatedAt": 1_700_000_100,
    "viewTokens": [{
        "tokenId": "t1a2b3",
        "name": "レビュー班",
        "fingerprint": "f718f51eef6786bb5814d57374155fc8",
        "expiresAt": 1_700_600_000,
        "status": "ACTIVE",
        "issuedAt": 1_700_000_000,
    }],
}

プロジェクトの記録 = {
    "projectId": "p7k2xq",
    "displayName": "設計レビュー",
    "projectKey": "design-review",
    "owner": "publisher-1",
    "scope": "SHARED",
    "status": "active",
    "memberArtifactIds": ["aaaaaaaa"],
    "viewTokens": [],
    "createdAt": 1_700_000_000,
    "updatedAt": 1_700_000_100,
}


# ── 保管から集約へ ──────────────────────────────────────

def test_保管の欄名が業務の語へ直る():
    """保管は name と呼び、業務は表示名と呼ぶ。結ぶのは repository だけ"""
    a = artifact_from_record(共有アーティファクトの記録)

    assert a.artifact_id.value == "aaaaaaaa"
    assert a.display_name == "検索基盤にPostgreSQLを採用する"
    assert a.published_by.value == "publisher-1"
    assert a.content_fingerprint == "c4a7c5c66b583eb3a49cb973802390c3"
    assert a.external_resource_count == 3


def test_平たく置かれた目印が一組にまとまる():
    """5つの値は一度に取り出され、一組についての規則がかかる"""
    d = artifact_from_record(共有アーティファクトの記録).descriptor

    assert d.document_id == "adr-search-backend"
    assert d.doc_type == "DecisionRecord"
    assert d.labels == ("backend", "search")
    assert d.source == EXTRACTED


def test_公開の状態が業務の語へ直る():
    """保管は active、業務は PUBLISHED。同じ概念の別の層の綴り"""
    assert artifact_from_record(共有アーティファクトの記録).status.value == PUBLISHED

    止めたもの = dict(共有アーティファクトの記録, status="disabled")
    assert artifact_from_record(止めたもの).status.value == SUSPENDED


def test_閲覧トークンが型として取り出される():
    t = artifact_from_record(共有アーティファクトの記録).view_tokens[0]

    assert t.token_id.value == "t1a2b3"
    assert t.name == "レビュー班"
    assert t.expires_at.value == 1_700_600_000
    assert t.status.value == ACTIVE
    assert t.is_usable(1_700_000_000)


def test_プロジェクトの所属は集約に入らない():
    """所属の正は共有アーティファクトの側。こちらの一覧は組み立て直せる投影"""
    p = project_from_record(プロジェクトの記録)

    assert not hasattr(p, "member_artifact_ids")
    assert p.project_id.value == "p7k2xq"
    assert p.scope.is_shared()
    assert p.status.value == PROJECT_PUBLISHED


# ── 集約から保管へ ──────────────────────────────────────

@pytest.mark.parametrize("記録,直す,戻す", [
    (共有アーティファクトの記録, artifact_from_record, artifact_to_record),
    (プロジェクトの記録, project_from_record, project_to_record),
])
def test_往復しても保管の記録は変わらない(記録, 直す, 戻す):
    """翻訳が片道でしか合っていないと、書き戻した時点で欄が消える"""
    assert 戻す(直す(記録), 記録) == 記録


def test_投影は書き戻しても失われない():
    """memberArtifactIds は集約の状態ではないが、記録からは消さない"""
    戻したもの = project_to_record(project_from_record(プロジェクトの記録), プロジェクトの記録)

    assert 戻したもの["memberArtifactIds"] == ["aaaaaaaa"]


def test_集約が知らない欄も書き戻しで残る():
    """wrapperHash は閲覧の面の関心事で集約の外にあるが、記録からは消さない"""
    戻したもの = artifact_to_record(artifact_from_record(共有アーティファクトの記録),
                                   共有アーティファクトの記録)

    assert 戻したもの["wrapperHash"] == "7a81f0974b8a6270b3b0fe1214143ca0"

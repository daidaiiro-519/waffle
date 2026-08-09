"""まとめが常に守ることを、不変条件シナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

「開ける／開けない」の最終的な判定は閲覧の面（エッジ側）が持つ。ここで確かめる
のは、業務の側が閲覧の面へ何を渡すか——渡していないものは開きようがない、
という一方の保証。閲覧の面そのものの振る舞いは受け口の契約テストが見る。

対象の仕様: agg-project（不変条件）
"""
from domain.value_objects import view_token
from domain.value_objects.view_token import ViewTokenFingerprint, ViewTokenId
from domain.value_objects.project import (
    PERSONAL,
    PUBLISHED,
    ProjectId,
    ProjectKey,
    ProjectOwner,
    ProjectScope,
    ProjectStatus,
)
from domain.entities.project import Project
from domain.value_objects.shared_artifact import (
    ArtifactDescriptor,
    ArtifactId,
    ArtifactStatus,
    PublisherId,
)
from domain.entities.shared_artifact import SharedArtifact
from domain.value_objects.shared_artifact import PUBLISHED as ARTIFACT_PUBLISHED

NOW = 1_700_000_000
P = "p7k2xq"
A = "aaaaaaaa"
B = "bbbbbbbb"
OWNER = "publisher-x"


def _project(tokens=(), status=PUBLISHED):
    return Project(
        project_id=ProjectId(P), display_name="まとめ", project_key=ProjectKey(),
        status=ProjectStatus(status), owner=ProjectOwner(OWNER),
        scope=ProjectScope(PERSONAL), created_at=NOW,
        view_tokens=tuple(tokens), updated_at=NOW)


def _artifact(artifact_id=A, projects=(), tokens=(), tags=()):
    return SharedArtifact(
        artifact_id=ArtifactId(artifact_id), display_name="文書",
        content_fingerprint="", view_tokens=tuple(tokens),
        status=ArtifactStatus(ARTIFACT_PUBLISHED), published_by=PublisherId(OWNER),
        descriptor=ArtifactDescriptor(labels=tuple(tags)), projects=tuple(projects),
        published_at=NOW, updated_at=NOW)


def _token(name="配布先", ttl=view_token.WEEK):
    return view_token.issued(ViewTokenId("t-" + name), name,
                            ViewTokenFingerprint("fingerprint-" + name),
                             view_token.expires_at(NOW, ttl), NOW)


def test_中身に書いた名前では所属できない():
    """
    Scenario: 中身に書いた名前では所属できない
    Given 共有アーティファクトBはプロジェクトPに加えられていない
    When 共有アーティファクトBの中身にPの名前を分類の目印として書いて差し替える
    Then 共有アーティファクトBはPに所属しないままである
    And Pの閲覧トークンで共有アーティファクトBは開けない
    """
    b = _artifact(B, projects=())

    revised = b.with_content("新しい指紋", ArtifactDescriptor(labels=(P,)), 0, NOW + 1)

    assert revised.projects == ()          # 目印を書いても所属は動かない
    assert P not in revised.projects       # 渡らないものは開きようがない


def test_入っていないものは開けない():
    """
    Scenario: 入っていないものは開けない
    Given 共有アーティファクトBはプロジェクトPに入っていない
    When Pの閲覧トークンで共有アーティファクトBを開こうとする
    Then 開けない
    """
    b = _artifact(B, projects=())

    assert P not in b.projects   # 閲覧の面へBがPの一員として渡ることはない


def test_共有アーティファクトの閲覧トークンを無効にしてもプロジェクト閲覧トークンは生きている():
    """
    Scenario: 共有アーティファクトの閲覧トークンを無効にしてもプロジェクト閲覧トークンは生きている
    Given 共有アーティファクトAがプロジェクトPに入っている
    When 共有アーティファクトAの閲覧トークンをすべて無効にする
    Then Pの閲覧トークンは引き続き使える
    And Pの閲覧トークンで共有アーティファクトAを開ける
    """
    project = _project(tokens=(_token("まとめの配布先"),))
    a = _artifact(A, projects=(P,), tokens=(_token("個別の配布先"),))

    emptied = a.with_view_tokens(view_token.all_revoked(a.view_tokens, NOW), NOW)

    assert view_token.usable(emptied.view_tokens, NOW) == ()
    assert len(view_token.usable(project.view_tokens, NOW)) == 1
    assert P in emptied.projects


def test_外しても共有アーティファクトは生き続ける():
    """
    Scenario: 外しても共有アーティファクトは生き続ける
    Given 共有アーティファクトAがプロジェクトPに入っている
    When 共有アーティファクトAをPから外す
    Then 共有アーティファクトAはそれ自身の閲覧トークンで引き続き開ける
    And Pの閲覧トークンでは共有アーティファクトAを開けない
    """
    a = _artifact(A, projects=(P,), tokens=(_token(),))

    left = a.left(P, NOW + 1)

    assert len(view_token.usable(left.view_tokens, NOW)) == 1
    assert left.projects == ()
    assert left.status.is_published()


def test_まとめを止めても中身は開ける():
    """
    Scenario: まとめを止めても中身は開ける
    Given プロジェクトPに共有アーティファクトAが入っている
    When プロジェクトPの公開を止める
    Then Pの閲覧トークンでは何も開けない
    And 共有アーティファクトAはそれ自身の閲覧トークンで開ける
    """
    project = _project(tokens=(_token("まとめの配布先"),))
    a = _artifact(A, projects=(P,), tokens=(_token("個別の配布先"),))

    stopped = project.suspended(NOW + 1)

    assert stopped.status.is_suspended()
    assert a.status.is_published()
    assert len(view_token.usable(a.view_tokens, NOW)) == 1

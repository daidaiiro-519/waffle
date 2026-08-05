"""共有アーティファクトが常に守ることを、不変条件シナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

テストダブルを使わない。不変条件は集約そのものが守るもので、外との結線を
挟むと、守っているのが集約なのか結線なのかが分からなくなる。

対象の仕様: agg-shared-artifact（不変条件）
"""
from domain import view_token
from domain.shared_artifact import (
    PUBLISHED, SUSPENDED, ArtifactDescriptor, ArtifactId, ArtifactStatus,
    PublisherId, SharedArtifact,
)

NOW = 1_700_000_000
A = "aaaaaaaa"
P = "p7k2xq"
OWNER = "publisher-x"


def _artifact(tokens=(), status=PUBLISHED, projects=(), fingerprint="もとの指紋"):
    return SharedArtifact(
        artifact_id=ArtifactId(A), display_name="文書",
        content_fingerprint=fingerprint, view_tokens=tuple(tokens),
        status=ArtifactStatus(status), published_by=PublisherId(OWNER),
        descriptor=ArtifactDescriptor(), projects=tuple(projects),
        published_at=NOW, updated_at=NOW)


def _token(name, ttl=view_token.WEEK, at=NOW):
    return view_token.issued(name, f"fingerprint-{name}",
                             view_token.expires_at(at, ttl), at)


def test_差し替えても中身は部分的に書き換わらない():
    """
    Scenario: 差し替えても中身は部分的に書き換わらない
    Given 共有アーティファクトAが公開されている
    When 新しい文書で中身を差し替える
    Then 中身は新しいものと完全に一致する
    And 差し替え前の中身の一部が残ることはない
    """
    a = _artifact(fingerprint="もとの指紋")

    revised = a.with_content("新しい指紋", ArtifactDescriptor(), 0, NOW + 1)

    assert revised.content_fingerprint == "新しい指紋"
    assert revised.content_fingerprint != a.content_fingerprint


def test_1本を無効にしても他の閲覧トークンは使える():
    """
    Scenario: 1本を無効にしても他の閲覧トークンは使える
    Given 2本の閲覧トークンが発行されている共有アーティファクト
    When 一方の閲覧トークンを無効にする
    Then 無効にした閲覧トークンでは開けない
    And もう一方の閲覧トークンでは開ける
    """
    first, second = _token("1人目"), _token("2人目")
    a = _artifact(tokens=(first, second))

    left = view_token.revoked(a.view_tokens, first.token_id.value)

    names = [t.name for t in view_token.usable(left, NOW)]
    assert names == ["2人目"]


def test_有効な閲覧トークンが5本あると発行できない():
    """
    Scenario: 有効な閲覧トークンが5本あると発行できない
    Given 有効な閲覧トークンが5本ある共有アーティファクト
    When 新しい閲覧トークンを発行しようとする
    Then 発行できない
    """
    tokens = tuple(_token(f"相手{i}") for i in range(view_token.MAX_ACTIVE))
    a = _artifact(tokens=tokens)

    assert not view_token.within_active_limit(a.view_tokens, NOW)


def test_期限を過ぎた閲覧トークンは上限に数えない():
    """
    Scenario: 期限を過ぎた閲覧トークンは上限に数えない
    Given 有効な閲覧トークンが4本あり、そのほかに期限を過ぎた閲覧トークンがある共有アーティファクト
    When 新しい閲覧トークンを発行する
    Then 発行できる
    """
    alive = tuple(_token(f"相手{i}", view_token.MONTH)
                  for i in range(view_token.MAX_ACTIVE - 1))
    expired = _token("切れた相手", view_token.WEEK)
    a = _artifact(tokens=alive + (expired,))

    later = NOW + view_token.WEEK + 1

    assert len(view_token.usable(a.view_tokens, later)) == view_token.MAX_ACTIVE - 1
    assert view_token.within_active_limit(a.view_tokens, later)


def test_再開しても期限内の閲覧トークンはそのまま使える():
    """
    Scenario: 再開しても期限内の閲覧トークンはそのまま使える
    Given 公開を止めた共有アーティファクトと、期限内で無効にされていない閲覧トークン
    When 公開を再開する
    Then その閲覧トークンで開ける
    """
    a = _artifact(tokens=(_token("配布先"),), status=SUSPENDED)

    resumed = a.resumed(NOW + 1)

    assert resumed.status.is_published()
    assert [t.name for t in view_token.usable(resumed.view_tokens, NOW)] == ["配布先"]


def test_差し替えても共有URLは変わらない():
    """
    Scenario: 差し替えても共有URLは変わらない
    Given 共有アーティファクトAの共有URLが閲覧者へ渡されている
    When 中身を差し替える
    Then 共有URLは変わらない
    And 閲覧者は同じ共有URLで新しい中身を見られる
    """
    a = _artifact()

    revised = a.with_content("新しい指紋", ArtifactDescriptor(), 0, NOW + 1)

    assert revised.artifact_id == a.artifact_id   # 共有URLはIDから決まる
    assert revised.content_fingerprint == "新しい指紋"


def test_分類の目印を書き換えても見られる相手は増えない():
    """
    Scenario: 分類の目印を書き換えても見られる相手は増えない
    Given 共有アーティファクトAはどのプロジェクトにも所属していない
    When 別のプロジェクトの名前を分類の目印として書いた中身へ差し替える
    Then そのプロジェクトの閲覧トークンでは開けないままである
    """
    a = _artifact(projects=())

    revised = a.with_content("新しい指紋", ArtifactDescriptor(labels=(P,)), 0, NOW + 1)

    assert revised.projects == ()
    assert revised.descriptor.labels == (P,)   # 目印としては控えるが、所属は動かない


def test_差し替えてもコメントが残る():
    """
    Scenario: 差し替えてもコメントが残る
    Given 共有アーティファクトAに3件のコメントが集まっている
    When 中身を差し替える
    Then 3件のコメントはいずれも残っている
    And 差し替えが行われた時点が区切りとして読み取れる

    コメントは別の集約が持つ。ここで確かめるのは、差し替えが集約の中に
    コメントへ触れる手立てを持たない——触れようがないこと。
    """
    a = _artifact()

    revised = a.with_content("新しい指紋", ArtifactDescriptor(), 0, NOW + 1)

    assert not hasattr(revised, "comments")
    assert revised.updated_at == NOW + 1   # 区切りの時点になる


def test_まとめて無効にすると全ての配布先が外れる():
    """
    Scenario: まとめて無効にすると全ての配布先が外れる
    Given 3本の閲覧トークンが発行されている共有アーティファクト
    When 閲覧トークンをまとめて無効にする
    Then どの閲覧トークンでも開けない
    And 公開そのものは止まっていない
    """
    a = _artifact(tokens=tuple(_token(f"{i}人目") for i in range(3)))

    emptied = a.with_view_tokens(view_token.all_revoked(a.view_tokens, NOW), NOW + 1)

    assert view_token.usable(emptied.view_tokens, NOW) == ()
    assert emptied.status.is_published()


def test_同じ名前の閲覧トークンは発行できない():
    """
    Scenario: 同じ名前の閲覧トークンは発行できない
    Given 「デザインチーム」という名前の有効な閲覧トークンがある共有アーティファクト
    When 同じ名前で新しい閲覧トークンを発行しようとする
    Then 発行できない
    """
    a = _artifact(tokens=(_token("デザインチーム"),))

    assert not view_token.name_is_free(a.view_tokens, "デザインチーム", NOW)
    assert view_token.name_is_free(a.view_tokens, "定例レビュー", NOW)


def test_1ヶ月を超える期限は与えられない():
    """
    Scenario: 1ヶ月を超える期限は与えられない
    Given 公開されている共有アーティファクト
    When 発行した時点から1ヶ月を超える期限で閲覧トークンを発行しようとする
    Then 発行できない
    """
    too_far = view_token.expires_at(NOW, view_token.MONTH + 1)
    within = view_token.expires_at(NOW, view_token.MONTH)

    assert not view_token.within_expiry_limit("artifact", NOW, too_far)
    assert view_token.within_expiry_limit("artifact", NOW, within)


def test_有効な閲覧トークンが1本も無くても公開は続く():
    """
    Scenario: 有効な閲覧トークンが1本も無くても公開は続く
    Given 閲覧トークンをまとめて無効にした共有アーティファクト
    When 公開状態を確かめる
    Then 公開は止まっていない
    """
    a = _artifact(tokens=())

    assert view_token.usable(a.view_tokens, NOW) == ()
    assert a.status.is_published()

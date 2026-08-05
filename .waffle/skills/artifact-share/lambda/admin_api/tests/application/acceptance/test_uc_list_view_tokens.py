"""いま誰に見せているかを確かめる操作を、受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

各テストの文書コメントは、仕様のシナリオを一字一句そのまま写したもの。
先頭の宣言行が突き合わせのキーで、続くGiven/When/Thenは、あとから仕様の
文言が変わったときに気づくための材料になる。

対象の仕様: uc-list-view-tokens
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from usecase_builder import build  # noqa: E402
from view_token_setup import AID, ME, NOW, issue, setup  # noqa: E402
from application.usecases.list_view_tokens import ListViewTokens  # noqa: E402
from domain import view_token  # noqa: E402
from domain.view_subject import ViewSubject  # noqa: E402

DAY = 24 * 60 * 60


def test_有効な閲覧トークンの名前と期限が返る():
    """
    Scenario: 有効な閲覧トークンの名前と期限が返る
    Given 「デザインチーム」と「定例レビュー」という名前の閲覧トークンがある対象
    When 一覧を求める
    Then 2つの名前と、それぞれの期限が返る
    """
    deps = setup()
    issue(deps, "デザインチーム", ttl=view_token.WEEK)
    issue(deps, "定例レビュー", ttl=DAY)

    got = build(deps, ListViewTokens).run(ME, ViewSubject.artifact(AID))

    assert sorted(t.name for t in got.view_tokens) == ["デザインチーム", "定例レビュー"]
    expires = {t.name: t.expires_at for t in got.view_tokens}
    assert expires["デザインチーム"] == NOW + view_token.WEEK
    assert expires["定例レビュー"] == NOW + DAY


def test_閲覧トークンそのものの値は返らない():
    """
    Scenario: 閲覧トークンそのものの値は返らない
    Given 閲覧トークンがある対象
    When 一覧を求める
    Then 閲覧トークンそのものの値は含まれていない
    """
    deps = setup()
    issued = issue(deps, "レビュー班", ttl=view_token.WEEK)

    got = build(deps, ListViewTokens).run(ME, ViewSubject.artifact(AID))

    row = got.view_tokens[0]
    assert not hasattr(row, "token")
    assert not hasattr(row, "fingerprint")
    assert issued.token not in repr(got)


def test_期限を過ぎた閲覧トークンは一覧に現れず記録も残らない():
    """
    Scenario: 期限を過ぎた閲覧トークンは一覧に現れず記録も残らない
    Given 有効な閲覧トークンが1本と、期限を過ぎた閲覧トークンが2本ある対象
    When 一覧を求める
    Then 返るのは有効な1本だけである
    And 期限を過ぎた閲覧トークンの記録は残っていない
    """
    deps = setup()
    issue(deps, "短い1", ttl=DAY)
    issue(deps, "短い2", ttl=DAY)

    later = NOW + DAY + 1
    issue(deps, "まだ使える", ttl=view_token.WEEK, at=later)

    got = build(deps.at(later), ListViewTokens).run(ME, ViewSubject.artifact(AID))

    assert [t.name for t in got.view_tokens] == ["まだ使える"]
    assert [t.name for t in deps.artifacts.find(AID).view_tokens] == ["まだ使える"]


def test_1本も無ければ空の一覧が返る():
    """
    Scenario: 1本も無ければ空の一覧が返る
    Given 有効な閲覧トークンが1本も無い対象
    When 一覧を求める
    Then 空の一覧が返る
    """
    deps = setup()

    got = build(deps, ListViewTokens).run(ME, ViewSubject.artifact(AID))

    assert got.view_tokens == ()

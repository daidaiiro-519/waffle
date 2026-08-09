"""招く・外す操作が守る約束を確かめる。

対象の仕様: uc-invite-publisher（操作保証）
"""
from publisher_setup import ADMIN, artifact_owned_by, setup
from application.usecases.invite_publisher import InvitePublisher
from application.usecases.list_publishers import ListPublishers
from usecase_builder import build


def test_外しても閲覧トークンは失効しない():
    """
    Scenario: 外しても閲覧トークンは失効しない
    Given 閲覧者が共有アーティファクトAの閲覧トークンを持っている
    When 管理者がAの投稿者を外す
    Then 閲覧者はそれまでの閲覧トークンでAを開ける
    """
    deps, _ = setup(objects=artifact_owned_by("publisher-2"))
    deps.keys.put("token:aaaaaaaa", "abc|0|1")
    before = dict(deps.keys.written)

    build(deps, InvitePublisher).run("remove", ADMIN, publisher_id="publisher-2")

    assert deps.keys.written == before


def test_招待が返す識別子は一覧のものと揃っている():
    """
    Scenario: 招待が返す識別子は一覧のものと揃っている
      Given 管理者がある宛先の人を招く
      When 続けて招かれている人を見渡す
      Then 招待が返した識別子と、一覧に並ぶその人の識別子が一致する

    宛先で入る設定のため、名簿の識別子は宛先そのものではない。
    """
    deps, _ = setup()

    invited = build(deps, InvitePublisher).run(
        "invite", ADMIN, email="new@example.com")
    listed = {row.id for row in build(deps, ListPublishers).run(ADMIN)}

    assert invited.publisher_id in listed

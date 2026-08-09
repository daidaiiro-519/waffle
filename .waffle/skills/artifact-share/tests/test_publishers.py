"""公開できる人の出し入れを、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-invite-publisher（受け入れ基準8件・エラー3件・操作保証2件）
名簿への接続は依存として渡す形にしてあるため、この検証では偽の名簿を渡す。
"""


import pytest

from usecase_builder import build  # noqa: E402
from application.usecases.invite_publisher import InvitePublisher  # noqa: E402
from application.usecases.list_publishers import ListPublishers  # noqa: E402

from application.ports import Caller  # noqa: E402

from shared.errors import PublisherError  # noqa: E402


from publisher_setup import (  # noqa: E402
    ADMIN, SOMEONE, setup,
)



def test_管理者でない者は外せない():
    deps, directory = setup()
    with pytest.raises(PublisherError) as x:
        build(deps, InvitePublisher).run("remove", SOMEONE, publisher_id="admin-1")
    assert x.value.code == "NOT_ADMINISTRATOR"
    assert directory.find("admin-1") is not None



def test_管理者でなければ送り直せない():
    deps, _ = setup(people={
        "admin-1": {"email": "admin@example.com", "status": "active"},
        "newbie": {"email": "new@example.com", "status": "invited"},
    })
    with pytest.raises(PublisherError) as x:
        build(deps, InvitePublisher).run("resend", Caller("newbie"), publisher_id="newbie")
    assert x.value.code == "NOT_ADMINISTRATOR"


def test_招かれていない人へは送り直せない():
    deps, _ = setup()
    with pytest.raises(PublisherError) as x:
        build(deps, InvitePublisher).run("resend", ADMIN, publisher_id="no-such-person")
    assert x.value.code == "PUBLISHER_NOT_FOUND"


def test_招待が返す識別子は一覧のものと揃っている():
    """揃っていないと、招いた直後に引き継ぎ先として指せない。
    宛先で入る設定のため、名簿の識別子は宛先そのものではない。"""
    deps, _ = setup()
    invited = build(deps, InvitePublisher).run("invite", ADMIN, email="new@example.com")

    listed = {r.id for r in build(deps, ListPublishers).run(ADMIN)}
    assert invited.publisher_id in listed

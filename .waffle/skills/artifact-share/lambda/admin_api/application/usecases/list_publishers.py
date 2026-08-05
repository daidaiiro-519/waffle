"""いま誰が公開できるのかを確かめる。

管理者だけが見られる。誰が招かれているかを投稿者どうしに見せないのは、共有の
相手を社外へ広げたときに、社内の顔ぶれまで一緒に伝わらないようにするため。

合言葉に関わるものは一切含めない。名簿が持っていても、ここから外へ出さない。

対象の仕様: uc-list-publishers
"""
from __future__ import annotations

from application.ports import Caller, PublisherDirectory
from domain.caller import may_manage_publishers
from shared.errors import PublisherError


def _require_admin(caller: Caller) -> None:
    """判定は domain が持つ。ここが決めるのは、断るときに何と伝えるかだけ。"""
    if not may_manage_publishers(caller):
        raise PublisherError("NOT_ADMINISTRATOR",
                             "投稿者を出し入れできるのは管理者だけです。")


def _list_publishers(directory: PublisherDirectory, caller: Caller) -> list[dict]:
    """招かれている人を並べる。管理者だけが見られる。

    誰が招かれているかを投稿者どうしに見せないのは、共有の相手を
    社外へ広げたときに、社内の顔ぶれまで一緒に伝わらないようにするため。

    合言葉に関わるものは一切含めない。名簿が持っていても、ここから外へ出さない。
    """
    _require_admin(caller)

    admins = set(directory.admins())
    rows = []
    for person in directory.list():
        email = person.get("email", "")
        rows.append({
            "id": person["id"],
            "name": email.split("@")[0] if email else person["id"],
            "email": email,
            "status": person.get("status", ""),
            "admin": person["id"] in admins,
        })
    return rows


class ListPublishers:
    """いま誰が公開できるのかを確かめる。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, directory: PublisherDirectory) -> None:
        self._directory = directory

    def run(self, caller: Caller) -> list[dict]:
        """このユースケースの唯一の入口。"""
        return _list_publishers(self._directory, caller)

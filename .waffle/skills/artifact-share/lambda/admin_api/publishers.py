"""公開できる人の出し入れ。

管理者が投稿者を招いたり外したりする。名簿そのものはこの文脈の外にあり、
ここは「誰が招けるか」と「外したとき何が起きてはならないか」だけを担う。

外しても、その人が公開した共有アーティファクトは公開されたまま残す。
閲覧者の手元の共有URLが、投稿者の異動という内輪の事情で黙って死んでは
ならないため。代わりに、引き継ぎ先が決まっていないものの件数を管理者へ
伝え、引き継ぐかどうかを人に決めさせる。

対象の仕様: uc-invite-publisher
"""

from __future__ import annotations

import json

from manage import Caller, Deps


class PublisherError(Exception):
    """操作できない理由を、仕様のエラーコードとともに伝える。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise PublisherError("NOT_ADMINISTRATOR",
                             "投稿者を出し入れできるのは管理者だけです。")


def invite(deps: Deps, caller: Caller, email: str) -> dict:
    """公開できる人を増やす。

    同じ宛先を重ねて招いても二重にはならず、その人の合言葉も、公開した
    ものも変わらない。招き直しが取り消しとして働いてはならないため。
    """
    _require_admin(caller)
    if not (email or "").strip():
        raise PublisherError("EMAIL_REQUIRED", "招く相手の宛先を入力してください。")

    publisher_id = deps.directory.invite(email.strip())
    return {"publisherId": publisher_id, "email": email.strip(),
            "event": "PublisherInvited"}


def remove(deps: Deps, caller: Caller, publisher_id: str) -> dict:
    """公開できる人から外す。公開したものには一切触れない。

    外したあと、その人が公開したもののうち引き継ぎ先が決まっていないものは
    誰も手入れできなくなる。件数を返し、引き継ぐかどうかは人に決めさせる。
    """
    _require_admin(caller)

    if publisher_id == caller.id:
        # 管理者が一人もいない状態へ落ちる経路を塞ぐ
        raise PublisherError("CANNOT_REMOVE_SELF", "自分自身は外せません。")

    if not deps.directory.find(publisher_id):
        raise PublisherError("PUBLISHER_NOT_FOUND", "その人は招かれていません。")

    orphaned = _count_artifacts(deps, publisher_id)
    deps.directory.remove(publisher_id)

    return {"publisherId": publisher_id, "orphanedArtifacts": orphaned,
            "event": "PublisherRemoved"}


def _count_artifacts(deps: Deps, publisher_id: str) -> int:
    """その人が公開した共有アーティファクトの件数。"""
    count = 0
    for key in deps.store.list("meta/"):
        try:
            meta = json.loads(deps.store.get(key))
        except Exception:
            continue
        if meta.get("uploadedBy") == publisher_id:
            count += 1
    return count

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

from shared.errors import PublisherError
from application.ports import Caller, ArtifactStore, PublisherDirectory
from application.ports.shared_artifact_repository import SharedArtifactRepository




def _require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise PublisherError("NOT_ADMINISTRATOR",
                             "投稿者を出し入れできるのは管理者だけです。")


def invite(directory: PublisherDirectory, caller: Caller, email: str) -> dict:
    """公開できる人を増やす。

    同じ宛先を重ねて招いても二重にはならず、その人の合言葉も、公開した
    ものも変わらない。招き直しが取り消しとして働いてはならないため。
    """
    _require_admin(caller)
    if not (email or "").strip():
        raise PublisherError("EMAIL_REQUIRED", "招く相手の宛先を入力してください。")

    publisher_id = directory.invite(email.strip())
    return {"publisherId": publisher_id, "email": email.strip(),
            "event": "PublisherInvited"}


def resend_invite(directory: PublisherDirectory, caller: Caller, publisher_id: str) -> dict:
    """招待をもう一度送る。仮の合言葉が新しくなる。

    招待に応じていない人は、利用者プールの再設定（合言葉を忘れたときの
    経路）を使えない。仮の合言葉を無くしたら本人には手立てが無いため、
    管理者が招き直す。

    既に入っている人へは送らない。送ると仮の合言葉に戻り、その人が自分で
    決めたものが使えなくなる。
    """
    _require_admin(caller)

    person = directory.find(publisher_id)
    if not person:
        raise PublisherError("PUBLISHER_NOT_FOUND", "その人は招かれていません。")
    if _status_of(person) != "invited":
        raise PublisherError("ALREADY_ACTIVE",
                             "その人はもう入っています。送り直すと、"
                             "本人が決めたパスワードが使えなくなります。")

    directory.resend(publisher_id)
    return {"publisherId": publisher_id, "event": "PublisherInvited"}


def _status_of(person) -> str:
    """名簿が返すものから、招待に応じたかどうかを読む。"""
    if isinstance(person, dict):
        return person.get("status", "")
    return getattr(person, "status", "")


def remove(artifacts: SharedArtifactRepository, store: ArtifactStore, directory: PublisherDirectory, caller: Caller, publisher_id: str) -> dict:
    """公開できる人から外す。公開したものには一切触れない。

    外したあと、その人が公開したもののうち引き継ぎ先が決まっていないものは
    誰も手入れできなくなる。件数を返し、引き継ぐかどうかは人に決めさせる。
    """
    _require_admin(caller)

    if publisher_id == caller.id:
        # 管理者が一人もいない状態へ落ちる経路を塞ぐ
        raise PublisherError("CANNOT_REMOVE_SELF", "自分自身は外せません。")

    if not directory.find(publisher_id):
        raise PublisherError("PUBLISHER_NOT_FOUND", "その人は招かれていません。")

    orphaned = _count_artifacts(artifacts, publisher_id)
    directory.remove(publisher_id)

    return {"publisherId": publisher_id, "orphanedArtifacts": orphaned,
            "event": "PublisherRemoved"}


def _count_artifacts(artifacts: SharedArtifactRepository, publisher_id: str) -> int:
    """その人が公開した共有アーティファクトの件数。"""
    found, _ = artifacts.all()
    return sum(1 for meta in found if meta.get("uploadedBy") == publisher_id)


def list_publishers(directory: PublisherDirectory, caller: Caller) -> list[dict]:
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

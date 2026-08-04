"""公開できる人の顔ぶれを、いまの体制に合わせる。

管理者が投稿者を招き、送り直し、外す。名簿そのものはこの文脈の外にあり、
ここは「誰が出し入れできるか」と「外したとき何が起きてはならないか」だけを担う。

外しても、その人が公開した共有アーティファクトは公開されたまま残す。閲覧者の
手元の共有URLが、投稿者の異動という内輪の事情で黙って死んではならないため。
代わりに、引き継ぎ先が決まっていないものの件数を管理者へ伝え、引き継ぐかどうかを
人に決めさせる。

対象の仕様: uc-invite-publisher
"""
from __future__ import annotations

from application.ports import Caller, PublisherDirectory
from application.ports.shared_artifact_repository import SharedArtifactRepository
from domain.publication import may_manage_publishers
from shared.errors import PublisherError


def _require_admin(caller: Caller) -> None:
    """判定は domain が持つ。ここが決めるのは、断るときに何と伝えるかだけ。"""
    if not may_manage_publishers(caller):
        raise PublisherError("NOT_ADMINISTRATOR",
                             "投稿者を出し入れできるのは管理者だけです。")


def _invite(directory: PublisherDirectory, caller: Caller, email: str) -> dict:
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


def _resend_invite(directory: PublisherDirectory, caller: Caller, publisher_id: str) -> dict:
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


def _remove(artifacts: SharedArtifactRepository, directory: PublisherDirectory, caller: Caller, publisher_id: str) -> dict:
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


class InvitePublisher:
    """公開できる人の顔ぶれを、いまの体制に合わせる。

    口はここで受け取り、操作のたびに渡し回さない。組み立てるのは合成ルートだけ。
    """

    def __init__(self, artifacts: SharedArtifactRepository, directory: PublisherDirectory) -> None:
        self._artifacts = artifacts
        self._directory = directory

    def run(self, operation: str, caller: Caller, email: str = "", publisher_id: str = "") -> dict:
        """このユースケースの唯一の入口。"""
        if operation == "invite":
            return _invite(self._directory, caller, email)
        if operation == "remove":
            return _remove(self._artifacts, self._directory, caller, publisher_id)
        if operation == "resend":
            return _resend_invite(self._directory, caller, publisher_id)
        raise ValueError(f"知らない操作です: {operation}")

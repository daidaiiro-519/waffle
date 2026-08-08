"""閲覧の面が判じるための材料を、鍵と値の保管へ書き出す。

ここに置いた値は、閲覧の面（CloudFront Functions の JavaScript）が同じ形で
読む。形の取り決めは infra/contract/token-records.json にあり、両方がそこを
読む。片方が形を直書きすると、もう片方を直したときに気づけない。

2026-08-01に、この形がずれたまま両側の検証が緑で通った。保管にはハッシュを
入れているのに、閲覧の面は平文と比べていた。実装も検証も同じ誤解で書かれて
おり、実環境でだけ「正しいトークンでも開けない」として現れた。

有効な記録は1つの値へ詰める。閲覧の面は1回の読み取りで区切って全件を突き
合わせるだけなので、本数の上限を知らない。先頭から決まった数しか読まない
実装にならないため、上限を伝え忘れて「投稿者には成功が返り閲覧者だけが
開けない」状態にはならない。上限は書き手だけが守る。

記録の並べ方（区切り・指紋の長さ・止めたことを表す綴り）と、対象ごとの鍵の
付け方はここだけが知る。
"""
from __future__ import annotations

import hashlib

from domain.view_subject import ARTIFACT, PROJECT, ViewSubject

# 記録どうしの区切りと、1件の中の欄の区切り
RECORD_SEPARATOR = ";"
FIELD_SEPARATOR = "|"

# 止めたことを表す記録。閲覧の面はこれを見たら通さない
CLOSED = "DISABLED"

# 照合に使う指紋の長さ。全体を残さないのは、記録の大きさを抑えるため
FINGERPRINT_LENGTH = 32

# 所属の区切り
MEMBERSHIP_SEPARATOR = " "

# 対象の種別ごとの鍵の頭
PREFIX = {ARTIFACT: "token:", PROJECT: "proj:"}
MEMBERSHIP_PREFIX = "pp:"


class KvsViewGate:
    """閲覧の面へ、いま誰が開けるのかを渡す。"""

    def __init__(self, keys):
        self._keys = keys

    def replace_grants(self, subject: ViewSubject, grants: list[tuple[str, int]]) -> None:
        """その対象を開けられる閲覧トークンを、この顔ぶれに置き換える。

        渡すのは（指紋, 期限）の並び。1本も無ければ、誰も開けないが公開は
        止まっていない状態になる——止めたこととは別の意味を持つ。
        """
        self._keys.put(_key(subject), RECORD_SEPARATOR.join(
            FIELD_SEPARATOR.join((fingerprint, str(expires_at)))
            for fingerprint, expires_at in grants))

    def close(self, subject: ViewSubject) -> None:
        """その対象を、どの閲覧トークンでも開けないようにする。"""
        self._keys.put(_key(subject), CLOSED)

    def fingerprint_of(self, token: str) -> str:
        """閲覧トークンを、照合にだけ使える形へ変える。元へは戻せない。"""
        return fingerprint(token)

    def set_membership(self, artifact_id: str, project_ids: list[str]) -> None:
        """その共有アーティファクトが、どのプロジェクトから開けるかを伝える。"""
        self._keys.put(f"{MEMBERSHIP_PREFIX}{artifact_id}",
                       MEMBERSHIP_SEPARATOR.join(project_ids))


def _key(subject: ViewSubject) -> str:
    return f"{PREFIX[subject.kind]}{subject.id}"


def fingerprint(token: str) -> str:
    """閲覧トークンから、照合にだけ使える形を作る。元へは戻せない。

    Args:
        token: 閲覧トークンそのものの値。

    Returns:
        照合にだけ使える形。元の値へは戻せない。

    Raises:
        なし。
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:FINGERPRINT_LENGTH]

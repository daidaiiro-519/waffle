"""閲覧の面が判じるための材料を、鍵と値の保管へ書き出す。

ここに置いた値は、閲覧の面（CloudFront Functions の JavaScript）が同じ形で
読む。形の取り決めは infra/contract/token-records.json にあり、両方がそこを
読む。片方が形を直書きすると、もう片方を直したときに気づけない。

2026-08-01に、この形がずれたまま両側の検証が緑で通った。保管にはハッシュを
入れているのに、閲覧の面は平文と比べていた。実装も検証も同じ誤解で書かれて
おり、実環境でだけ「正しいトークンでも開けない」として現れた。

記録の並べ方（区切り・指紋の長さ・止めたことを表す綴り）と、対象ごとの鍵の
付け方はここだけが知る。application は「開けるようにする・止める」としか
言わない。
"""
from __future__ import annotations

import hashlib

from domain.view_subject import ARTIFACT, PROJECT, ViewSubject

# 記録の区切り。閲覧の面も同じ区切りで分ける
SEPARATOR = "|"

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
    def __init__(self, keys):
        self._keys = keys

    def allow(self, subject: ViewSubject, token: str, at: int,
              ttl: int = 0, generation: int = 1) -> None:
        self._keys.put(_key(subject), _record(token, at, ttl, generation))

    def close(self, subject: ViewSubject) -> None:
        self._keys.put(_key(subject), CLOSED)

    def generation_of(self, subject: ViewSubject) -> int:
        try:
            record = self._keys.get(_key(subject))
        except Exception:
            return 1
        if not record or record == CLOSED:
            return 1
        parts = record.split(SEPARATOR)
        return int(parts[2]) if len(parts) > 2 else 1

    def set_membership(self, artifact_id: str, project_ids: list[str]) -> None:
        self._keys.put(f"{MEMBERSHIP_PREFIX}{artifact_id}",
                       MEMBERSHIP_SEPARATOR.join(project_ids))


def _key(subject: ViewSubject) -> str:
    return f"{PREFIX[subject.kind]}{subject.id}"


def _record(token: str, at: int, ttl: int, generation: int) -> str:
    """保管へ残す記録を組み立てる。閲覧の面はこれを分けて読む。"""
    return SEPARATOR.join((fingerprint(token),
                           str(at + ttl if ttl > 0 else 0),
                           str(generation)))


def fingerprint(token: str) -> str:
    """閲覧トークンから、照合にだけ使える形を作る。元へは戻せない。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:FINGERPRINT_LENGTH]

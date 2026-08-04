"""閲覧トークンと、保管に残すその記録の形。

トークンそのものは残さない。残すのは照合できる形だけで、保管を読めた者が
そこから閲覧できるようにはしない。

記録には有効期限と世代番号を添える。再発行しただけでは閲覧者の手元にある
記録が生き残るため、照合の側は値と世代の両方が一致したときだけ通す。

この記録の形は、閲覧の面（別のランタイム）も同じものを読む。形の宣言は
spec に1つだけ置き、実装だけがランタイムごとに分かれる。

対象の仕様: agg-shared-artifact / uc-reissue-view-token
"""
from __future__ import annotations

import hashlib

from domain.identifier import random_chars

TOKEN_GROUPS = 3
TOKEN_GROUP_LENGTH = 4

# 既定の有効期限（秒）。0 は無期限
DEFAULT_TOKEN_TTL = 0

# 記録の区切り。閲覧の面も同じ形を読む
SEPARATOR = "|"

# 公開を止めたことを表す記録。照合の側はこれを見たら通さない
DISABLED = "DISABLED"

# 照合に使う指紋の長さ。全体を残さないのは、記録の大きさを抑えるため
FINGERPRINT_LENGTH = 32


def new_token() -> str:
    """閲覧トークンを発行する。

    区切って読みやすくするのは、口頭やチャットで渡されることがあるため。
    """
    return "-".join(random_chars(TOKEN_GROUP_LENGTH) for _ in range(TOKEN_GROUPS))


def token_record(token: str, now: int, ttl: int = DEFAULT_TOKEN_TTL,
                 generation: int = 1) -> str:
    """トークンの保管に残す記録を組み立てる。"""
    return SEPARATOR.join((
        fingerprint(token),
        str(now + ttl if ttl > 0 else 0),
        str(generation),
    ))


def fingerprint(token: str) -> str:
    """トークンから、照合にだけ使える形を作る。元へは戻せない。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:FINGERPRINT_LENGTH]


def generation_of(record: str | None, default: int = 1) -> int:
    """記録から世代番号を読む。

    止めた記録・空の記録・世代を持たない古い形の記録は、いずれも default を
    返す。読めないことと世代が無いことを区別しないのは、どちらの場合も
    次に発行する世代を呼び出し側が同じように決めるため。
    """
    if not record or record == DISABLED:
        return default
    parts = record.split(SEPARATOR)
    return int(parts[2]) if len(parts) > 2 else default

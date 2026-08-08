"""閲覧トークンと、1つの対象が同時に持てるその顔ぶれ。

渡した相手の手元にしか無い状態を保つことが、これが鍵として働く前提になる。
だから保管には残さず、照合できる形（指紋）だけを残す。その形をどう作り、
どう並べるかは閲覧の面との取り決めであり、ここには現れない。

1本が1つの配布先を表す。相手ごとに別々に渡し、あとから1本だけ外せることが
この仕組みの要で、外す操作が使いにくいと結局使われなくなる。

期限を必ず持たせるのは、渡した相手を外す手立てが人手の操作だけだと、押し忘れた
ときに渡したものが永久に開き続けるため。期限は各配信の口が自分の時計で判じる
ので、無効化の伝わりを待たずに効く唯一の手立てになる。

2つの集約が同じ形の閲覧トークンを持ち、宣言も両方に同じ名前で並んでいる。
ここへ1つだけ置いて共有する——集約ごとのファイルへ写すと同じ語が2回定義され、
語彙の一貫性そのものが壊れる。

対象の仕様: agg-shared-artifact / agg-project / uc-issue-view-token /
uc-list-view-tokens / uc-revoke-view-token / uc-revoke-all-view-tokens
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from domain.identifier import random_chars

TOKEN_GROUPS = 3
TOKEN_GROUP_LENGTH = 4
TOKEN_ID_LENGTH = 6

WEEK = 7 * 24 * 60 * 60
MONTH = 30 * 24 * 60 * 60

# 期限を指定しなかったときの有効期間
DEFAULT_TTL = WEEK

# 期限なしを表す値
NO_EXPIRY = 0

ACTIVE = "ACTIVE"
REVOKED = "REVOKED"

# 同時に有効な閲覧トークンの上限。どれを外すかは公開した人が一覧から選ぶ操作
# なので、選べる数に収まっている必要がある
MAX_ACTIVE = 5


# ── 値 ──────────────────────────────────────────────────

@dataclass(frozen=True)
class ViewTokenId:
    """1本の閲覧トークンを、対象の中で一意に指す識別子。

    閲覧トークンそのものの値とは別で、こちらは公開した人が一覧で見て選ぶために
    使う。無効化しても変わらない。
    """

    value: str


@dataclass(frozen=True)
class ViewTokenExpiry:
    """1本の閲覧トークンが使えなくなる時点。0 は期限なしを表す。"""

    value: int = NO_EXPIRY

    def is_endless(self) -> bool:
        return self.value == NO_EXPIRY

    def has_passed(self, now: int) -> bool:
        return not self.is_endless() and self.value <= now


@dataclass(frozen=True)
class ViewTokenStatus:
    """使える状態にあるかどうか。ACTIVE と REVOKED のいずれか。

    無効にすると REVOKED になり、元へは戻らない。
    """

    value: str = ACTIVE

    def is_active(self) -> bool:
        return self.value == ACTIVE


@dataclass(frozen=True)
class ViewToken:
    """渡した相手1つ分の閲覧トークン。値そのものは持たず、照合できる形だけを持つ。"""

    token_id: ViewTokenId
    name: str
    fingerprint: str
    expires_at: ViewTokenExpiry
    status: ViewTokenStatus
    issued_at: int

    def is_usable(self, now: int) -> bool:
        """いま使えるか。無効にされておらず、期限を過ぎていないこと。"""
        return self.status.is_active() and not self.expires_at.has_passed(now)

    def revoked(self) -> "ViewToken":
        return replace(self, status=ViewTokenStatus(REVOKED))


# 集約ごとの呼び分け。形は同じで、指している相手だけが違う
ArtifactViewToken = ViewToken
ProjectViewToken = ViewToken


# ── 発行 ────────────────────────────────────────────────

def new_token() -> str:
    """閲覧トークンを発行する。

    区切って読みやすくするのは、口頭やチャットで渡されることがあるため。

    Returns:
        渡す相手に見せる閲覧トークンそのものの値。

    Raises:
        なし。
    """
    return "-".join(random_chars(TOKEN_GROUP_LENGTH) for _ in range(TOKEN_GROUPS))


def expires_at(now: int, ttl: int | None = None) -> ViewTokenExpiry:
    """いつ使えなくなるか。省いたときは既定の有効期間を与える。

    Args:
        now: 発行する時点。
        ttl: 有効期間。省くと既定の有効期間を使う。

    Returns:
        使えなくなる時点。

    Raises:
        なし。
    """
    if ttl is None:
        ttl = DEFAULT_TTL
    return ViewTokenExpiry(now + ttl if ttl > 0 else NO_EXPIRY)


def issued(name: str, fingerprint: str, expiry: ViewTokenExpiry, at: int) -> ViewToken:
    """発行した1本。閲覧トークンそのものの値は含めない。

    Args:
        name: この1本に付ける名前。
        fingerprint: 照合にだけ使える形。
        expiry: 使えなくなる時点。
        at: 発行した時点。

    Returns:
        発行した閲覧トークン1本。

    Raises:
        なし。
    """
    return ViewToken(
        token_id=ViewTokenId(random_chars(TOKEN_ID_LENGTH)),
        name=name,
        fingerprint=fingerprint,
        expires_at=expiry,
        status=ViewTokenStatus(ACTIVE),
        issued_at=at,
    )


# ── 顔ぶれを見る・変える ────────────────────────────────

def usable(tokens: tuple[ViewToken, ...], now: int) -> tuple[ViewToken, ...]:
    """いま使えるものだけを、渡した順のまま返す。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        now: いまの時点。

    Returns:
        いま使えるものだけを、渡した順のまま並べたもの。

    Raises:
        なし。
    """
    return tuple(t for t in tokens or () if t.is_usable(now))


def within_active_limit(tokens: tuple[ViewToken, ...], now: int) -> bool:
    """これ以上増やせるか。期限を過ぎたものは数に含めない。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        now: いまの時点。

    Returns:
        これ以上増やせれば True。期限を過ぎたものは数に含めない。

    Raises:
        なし。
    """
    return len(usable(tokens, now)) < MAX_ACTIVE


def name_is_free(tokens: tuple[ViewToken, ...], name: str, now: int) -> bool:
    """その名前をまだ使っていないか。

    名前は、どれを外すかを公開した人が選ぶための手がかりなので、有効なものの
    中で重なってはいけない。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        name: 使おうとしている名前。
        now: いまの時点。

    Returns:
        まだ使っていなければ True。

    Raises:
        なし。
    """
    return all(t.name != name for t in usable(tokens, now))


def without_expired(tokens: tuple[ViewToken, ...], now: int) -> tuple[ViewToken, ...]:
    """期限を過ぎたものの記録を取り除く。

    残しても外す対象にはならず、一覧を埋めて選びにくくするだけ。見る側からは
    期限切れと初めから無いものを区別しないので、記録の有無は開けるかどうかに
    影響しない。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        now: いまの時点。

    Returns:
        期限を過ぎたものの記録を取り除いた顔ぶれ。

    Raises:
        なし。
    """
    return tuple(t for t in tokens or ()
                 if not t.status.is_active() or t.is_usable(now))


def revoked(tokens: tuple[ViewToken, ...], token_id: str) -> tuple[ViewToken, ...]:
    """その1本だけを使えなくする。他はそのまま。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        token_id: 使えなくする1本の識別子。

    Returns:
        その1本だけを使えなくした顔ぶれ。

    Raises:
        なし。
    """
    return tuple(t.revoked() if t.token_id.value == token_id else t
                 for t in tokens or ())


def all_revoked(tokens: tuple[ViewToken, ...], now: int) -> tuple[ViewToken, ...]:
    """いま使えるものをすべて使えなくする。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        now: いまの時点。

    Returns:
        いま使えるものをすべて使えなくした顔ぶれ。

    Raises:
        なし。
    """
    return tuple(t.revoked() if t.is_usable(now) else t for t in tokens or ())


def grants(tokens: tuple[ViewToken, ...], now: int) -> list[tuple[str, int]]:
    """閲覧の面へ渡す顔ぶれ。使えるものだけを（照合の形, 期限）で並べる。

    Args:
        tokens: 対象の閲覧トークンの顔ぶれ。
        now: いまの時点。

    Returns:
        使えるものだけを（照合の形, 期限）の組で並べたもの。

    Raises:
        なし。
    """
    return [(t.fingerprint, t.expires_at.value) for t in usable(tokens, now)]

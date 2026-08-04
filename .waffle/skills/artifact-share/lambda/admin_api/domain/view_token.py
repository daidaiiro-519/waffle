"""閲覧トークン。

渡した相手の手元にしか無い状態を保つことが、これが鍵として働く前提になる。
だから保管には残さず、照合できる形（指紋）だけを残す。その形をどう作り、
どう並べるかは保管の側の取り決めであり、ここには現れない。

期限を必ず持たせるのは、渡した相手を外す手立てが人手の操作だけだと、押し忘れた
ときに渡したものが永久に開き続けるため。期限は各配信の口が自分の時計で判じる
ので、無効化の伝わりを待たずに効く唯一の手立てになる。

対象の仕様: agg-shared-artifact / uc-issue-view-token
"""
from __future__ import annotations

from domain.identifier import random_chars

TOKEN_GROUPS = 3
TOKEN_GROUP_LENGTH = 4

# 既定の有効期間（秒）。0 は期限なし
DEFAULT_TOKEN_TTL = 0


def new_token() -> str:
    """閲覧トークンを発行する。

    区切って読みやすくするのは、口頭やチャットで渡されることがあるため。
    """
    return "-".join(random_chars(TOKEN_GROUP_LENGTH) for _ in range(TOKEN_GROUPS))


def expires_at(now: int, ttl: int = DEFAULT_TOKEN_TTL) -> int:
    """いつ使えなくなるか。0 は期限なしを表す。"""
    return now + ttl if ttl > 0 else 0

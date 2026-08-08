"""利用者の証明を検証する。

管理画面が持ってきた証明が、この環境の利用者プールが招いた人へ確かに
出したものかを確かめ、誰であるか（と管理者かどうか）を返す。

ここが唯一の関所になる。招かれた者だけが公開できるという前提は、この
検証が正しいことにすべて乗っている。

外部への接続（公開鍵の取得）は依存として受け取る。中核の判定は渡された
ものだけを使うため、検証のときは偽の依存を渡せる。

対象の仕様: uc-publish-artifact / bc-artifact-share（投稿者・管理者）
"""

from __future__ import annotations

import base64
import json
import time
import urllib.request
from typing import Callable

# 受け付ける署名方式。利用者プールが出すものはこれひとつ
ALGORITHM = "RS256"

# 公開鍵を取り直す間隔（秒）。鍵は滅多に変わらないが、変わったときに
# 呼び出しのたび取りに行かずに済ませる
JWKS_TTL = 3600


def _b64(segment: str) -> bytes:
    """URL用のbase64を戻す。末尾の詰め物は落とされている。"""
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def verify(authorization: str, pool_id: str, client_id: str,
           verify_signature: Callable[[bytes, bytes, str], bool] | None = None) -> dict | None:
    """証明を検証し、{"username", "groups"} を返す。通せないものは None。

    通す条件は5つ。署名が合っていること、期限が切れていないこと、この
    利用者プールが出したものであること、このアプリ向けであること、
    そして誰であるかを示す用途のものであること。

    どれか1つでも欠けたら None を返す。理由を呼び出し元へ細かく伝えない
    のは、どこまで合っていたのかを外から探れないようにするため。

    Args:
        authorization: 受け取った証明。
        pool_id: 証明を発行した側の識別子。
        client_id: 宛先として期待する識別子。
        verify_signature: 署名を検証する処理。

    Returns:
        利用者名と所属を持つ辞書。通せないものは None。

    Raises:
        なし。
    """
    token = (authorization or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        return None

    try:
        header = json.loads(_b64(parts[0]))
        claims = json.loads(_b64(parts[1]))
        signature = _b64(parts[2])
    except Exception:
        return None

    # 署名方式を証明の側に選ばせない。none を名乗って署名を空にする細工を拒む
    if header.get("alg") != ALGORITHM:
        return None

    if verify_signature is None:
        verify_signature = signature_verifier(_jwks_loader(pool_id))
    message = (parts[0] + "." + parts[1]).encode("ascii")
    if not verify_signature(message, signature, header.get("kid", "")):
        return None

    now = int(time.time())
    # 期限には猶予を持たせない。切れているものは切れているものとして扱う
    if not isinstance(claims.get("exp"), int) or claims["exp"] <= now:
        return None

    region = pool_id.split("_")[0]
    expected_issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    if claims.get("iss") != expected_issuer:
        return None

    if claims.get("aud") != client_id:
        return None

    # 誰であるかを示す用途のものだけを受け取る。アクセス用のものは名前を持たない
    if claims.get("token_use") != "id":
        return None

    username = claims.get("cognito:username") or claims.get("sub")
    if not username:
        return None

    return {"username": username, "groups": list(claims.get("cognito:groups") or [])}


# ── 署名の検証 ──────────────────────────────────────────

def signature_verifier(load_jwks: Callable[[], dict]) -> Callable[[bytes, bytes, str], bool]:
    """公開鍵の一覧を取ってくる手段を受け取り、署名を検証する処理を返す。

    Args:
        load_jwks: 公開鍵の一覧を取ってくる手段。

    Returns:
        署名を検証する処理。

    Raises:
        なし。
    """

    def check(message: bytes, signature: bytes, kid: str) -> bool:
        key = _find_key(load_jwks(), kid)
        if not key:
            return False
        try:
            return _rsa_pkcs1_sha256(message, signature, key["n"], key["e"])
        except Exception:
            return False

    return check


def _find_key(jwks: dict, kid: str) -> dict | None:
    for key in (jwks or {}).get("keys", []):
        if key.get("kid") == kid and key.get("kty") == "RSA":
            return key
    return None


def _rsa_pkcs1_sha256(message: bytes, signature: bytes, n_b64: str, e_b64: str) -> bool:
    """RSAの公開鍵で署名を検証する。

    外部の部品を足さずに済ませるため、復号したものが本来の形と一致するかを
    そのまま突き合わせる。比較は先頭から順に打ち切らず、全体を見てから
    答えを出す（どこまで合っていたかを応答の速さから読み取らせないため）。
    """
    import hashlib
    import hmac

    n = int.from_bytes(_b64(n_b64), "big")
    e = int.from_bytes(_b64(e_b64), "big")
    size = (n.bit_length() + 7) // 8

    if len(signature) != size:
        return False

    decoded = pow(int.from_bytes(signature, "big"), e, n).to_bytes(size, "big")

    # SHA-256 を指す印。復号したものはこの形になっているはず
    prefix = bytes.fromhex("3031300d060960864801650304020105000420")
    digest = hashlib.sha256(message).digest()
    expected = (b"\x00\x01" + b"\xff" * (size - len(prefix) - len(digest) - 3)
                + b"\x00" + prefix + digest)

    return hmac.compare_digest(decoded, expected)


# ── 公開鍵の取得 ────────────────────────────────────────

_cache: dict = {"at": 0, "jwks": None}


def _jwks_loader(pool_id: str) -> Callable[[], dict]:  # pragma: no cover - 外部への接続
    region = pool_id.split("_")[0]
    url = (f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
           "/.well-known/jwks.json")

    def load() -> dict:
        now = int(time.time())
        if _cache["jwks"] and now - _cache["at"] < JWKS_TTL:
            return _cache["jwks"]
        with urllib.request.urlopen(url, timeout=5) as res:
            _cache["jwks"] = json.loads(res.read().decode("utf-8"))
            _cache["at"] = now
        return _cache["jwks"]

    return load

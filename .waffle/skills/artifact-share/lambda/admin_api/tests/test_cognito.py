"""利用者の証明の検証を確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

ここが通す・通さないの判断を誤ると、招かれていない人が公開できたり、
投稿者が管理者として扱われたりする。鍵の取得だけを依存として差し替え、
検証そのものは実物の処理を通す。

対象の仕様: uc-publish-artifact（招かれた者だけが公開できる）、
および管理者の判定（bc-artifact-share の管理者）
"""

import base64
import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cognito  # noqa: E402

POOL = "ap-northeast-1_abc123"
CLIENT = "client-1"
ISSUER = f"https://cognito-idp.ap-northeast-1.amazonaws.com/{POOL}"


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def token(payload: dict, header: dict | None = None, signature: bytes = b"sig") -> str:
    head = {"alg": "RS256", "kid": "key-1", **(header or {})}
    return ".".join([
        b64(json.dumps(head).encode()),
        b64(json.dumps(payload).encode()),
        b64(signature),
    ])


def claims(**over) -> dict:
    now = int(time.time())
    base = {"iss": ISSUER, "aud": CLIENT, "token_use": "id",
            "cognito:username": "publisher-1", "exp": now + 600, "iat": now}
    base.update(over)
    return base


class FakeVerifier:
    """署名の検証だけを差し替える。合っていることにする／していないことにする。"""

    def __init__(self, ok=True):
        self.ok = ok
        self.seen = []

    def __call__(self, message, signature, kid):
        self.seen.append(kid)
        return self.ok


def verify(tok, verifier=None, pool=POOL, client=CLIENT):
    return cognito.verify(tok, pool, client, verify_signature=verifier or FakeVerifier())


# ── 通すもの ────────────────────────────────────────────

def test_正しい証明なら誰であるかを返す():
    got = verify(token(claims()))
    assert got["username"] == "publisher-1"
    assert got["groups"] == []


def test_グループが入っていれば取り出す():
    got = verify(token(claims(**{"cognito:groups": ["administrators"]})))
    assert got["groups"] == ["administrators"]


def test_署名の検証には証明が名乗る鍵の識別子を渡す():
    v = FakeVerifier()
    verify(token(claims(), header={"kid": "key-9"}), verifier=v)
    assert v.seen == ["key-9"]


# ── 通さないもの ────────────────────────────────────────

def test_署名が合わなければ通さない():
    assert verify(token(claims()), verifier=FakeVerifier(ok=False)) is None


def test_期限が切れていれば通さない():
    assert verify(token(claims(exp=int(time.time()) - 1))) is None


def test_別の利用者プールが出したものは通さない():
    other = ISSUER.replace(POOL, "ap-northeast-1_zzz999")
    assert verify(token(claims(iss=other))) is None


def test_別のアプリ向けに出されたものは通さない():
    assert verify(token(claims(aud="other-client"))) is None


def test_用途が違うものは通さない():
    """誰であるかを示す証明だけを受け付ける（アクセス用のものは名前を持たない）"""
    assert verify(token(claims(token_use="access"))) is None


def test_署名の無いものは通さない():
    """alg を none にして署名を空にする細工を拒む"""
    tok = token(claims(), header={"alg": "none"}, signature=b"")
    assert verify(tok) is None


def test_形が違うものは通さない():
    for bad in ("", "abc", "a.b", "a.b.c.d", "Bearer "):
        assert verify(bad) is None


def test_中身が壊れていても落ちない():
    assert verify("aaa.bbb.ccc") is None


def test_接頭辞つきでも受け取れる():
    """要求の見出しは 'Bearer xxx' の形で届く"""
    assert verify("Bearer " + token(claims()))["username"] == "publisher-1"


# ── 署名の検証そのもの ──────────────────────────────────

def test_公開鍵から署名を検証できる():
    """RSAの公開鍵の材料（n・e）から、実際の署名を検証できることを確かめる"""
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = key.public_key().public_numbers()

    def to_b64(value: int) -> str:
        return b64(value.to_bytes((value.bit_length() + 7) // 8, "big"))

    jwks = {"keys": [{"kid": "key-1", "kty": "RSA",
                      "n": to_b64(numbers.n), "e": to_b64(numbers.e)}]}

    payload = claims()
    message = ".".join([b64(json.dumps({"alg": "RS256", "kid": "key-1"}).encode()),
                        b64(json.dumps(payload).encode())])
    signature = key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA256())
    tok = message + "." + b64(signature)

    verifier = cognito.signature_verifier(lambda: jwks)
    assert cognito.verify(tok, POOL, CLIENT, verify_signature=verifier)["username"] == "publisher-1"

    # 中身を1文字でも変えれば通らない
    broken = tok[:-4] + ("aaaa" if not tok.endswith("aaaa") else "bbbb")
    assert cognito.verify(broken, POOL, CLIENT, verify_signature=verifier) is None

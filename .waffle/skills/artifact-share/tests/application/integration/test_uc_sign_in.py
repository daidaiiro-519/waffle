"""入るという操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

こちらが担うのは関所ひとつ。名簿が出したものでない証明を通さないこと、
そして合言葉をこちら側に残さないこと。

対象の仕様: uc-sign-in（操作保証）
"""
import base64
import json
import re
import time
from pathlib import Path

import adapters.outbound.cognito as cognito

SKILL = Path(__file__).resolve().parents[3]
LAMBDA = SKILL / "lambda" / "admin_api"
ADMIN_APP = (SKILL / "scripts" / "app" / "app.js").read_text(encoding="utf-8")

POOL = "ap-northeast-1_abc123"
CLIENT = "client-1"
ISSUER = f"https://cognito-idp.ap-northeast-1.amazonaws.com/{POOL}"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _token(payload: dict) -> str:
    head = {"alg": "RS256", "kid": "key-1"}
    return ".".join([_b64(json.dumps(head).encode()),
                     _b64(json.dumps(payload).encode()), _b64(b"sig")])


def _claims(**over) -> dict:
    now = int(time.time())
    base = {"iss": ISSUER, "aud": CLIENT, "token_use": "id",
            "cognito:username": "publisher-1", "exp": now + 600, "iat": now}
    base.update(over)
    return base


def _verify(tok, signature_ok=True, pool=POOL, client=CLIENT):
    return cognito.verify(tok, pool, client,
                          verify_signature=lambda *_: signature_ok)


def test_合言葉はどこにも残らない():
    """
    Scenario: 合言葉はどこにも残らない
    Given ある人が合言葉を示して入っている
    When この文脈が持つものを調べる
    Then 合言葉も、そこから合言葉を導けるものも見つからない
    """
    # 合言葉の値を受け取る口も、持つ欄も無い。状態の名前（FORCE_CHANGE_PASSWORD）や
    # 操作の名前（reset-password）は値ではないので、値として扱う形だけを見る
    holding = re.compile(r"""(?ix)
        (\bpassword\s*[:=][^=]        # password という欄・変数への代入
        |\[["']password["']\]          # 要求から password を取り出す
        |\.get\(\s*["']password["']    # 同上
        |\bpassword\s*[,)])            # password を引数として渡す
    """)
    sources = list((LAMBDA / "application").rglob("*.py"))
    sources += list((LAMBDA / "domain").rglob("*.py"))
    sources += list((LAMBDA / "adapters").rglob("*.py"))
    for path in sources:
        found = holding.findall(path.read_text(encoding="utf-8"))
        assert found == [], f"{path}: {found}"

    # 画面の側も、渡したあとは持ち物から消す
    assert "clearSecrets" in ADMIN_APP


def test_証明の出どころは名簿ひとつ():
    """
    Scenario: 証明の出どころは名簿ひとつ
    Given 名簿が出したものではない証明が示される
    When その証明で操作しようとする
    Then 誰とも特定されず、操作は拒まれる
    """
    # 署名が合っていない
    assert _verify(_token(_claims()), signature_ok=False) is None
    # 別の利用者プールが出した
    assert _verify(_token(_claims(iss="https://example.com/other"))) is None
    # 別のアプリ向け
    assert _verify(_token(_claims(aud="other-client"))) is None
    # 誰であるかを示す用途ではない
    assert _verify(_token(_claims(token_use="access"))) is None
    # 期限が切れている
    assert _verify(_token(_claims(exp=int(time.time()) - 1))) is None

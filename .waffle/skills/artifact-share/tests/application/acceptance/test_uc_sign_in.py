"""入るという操作のうち、この文脈が担う分を確かめる。

実行:  python3 -m pytest tests/ -v

合言葉そのものの照合・仮の合言葉の決め直し・入り直すための券は、投稿者の名簿
（この文脈の外にある仕組み）が行う。こちらが担うのは、名簿が出した証明を検証
すること、そこから肩書きを読むこと、合言葉を残さないこと、そして名簿へ渡す
設定を出荷すること。

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-sign-in
"""
import base64
import json
import re
import time
from pathlib import Path

import adapters.outbound.cognito as cognito

SKILL = Path(__file__).resolve().parents[3]
CLOUDFORMATION = (SKILL / "infra" / "cloudformation.yaml").read_text(encoding="utf-8")
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


def _verify(tok, signature_ok=True):
    return cognito.verify(tok, POOL, CLIENT,
                          verify_signature=lambda *_: signature_ok)


def test_管理者かどうかが証明に含まれる():
    """
    Scenario: 管理者かどうかが証明に含まれる
    Given 管理者が招かれている
    When その人が入る
    Then 返る証明に、管理者であることが含まれている
    """
    admin_group = re.search(r"GroupName:\s*(\S+)", CLOUDFORMATION).group(1)

    who = _verify(_token(_claims(**{"cognito:groups": [admin_group]})))

    assert who["username"] == "publisher-1"
    assert admin_group in who["groups"]


def test_決められた強さの設定を出荷する():
    """
    Scenario: 決められた強さの設定を出荷する
    Given 利用者プールの設定を出荷する
    When その設定を確かめる
    Then 決められた合言葉の強さが含まれている

    強さを決めて守るのは名簿だが、その設定を渡すのはこちらの出荷物。
    ここが消えれば、弱い合言葉が通るようになる。
    """
    policy = CLOUDFORMATION[CLOUDFORMATION.index("PasswordPolicy:"):][:400]

    assert int(re.search(r"MinimumLength:\s*(\d+)", policy).group(1)) >= 12
    for kind in ("Uppercase", "Lowercase", "Numbers"):
        assert re.search(rf"Require{kind}:\s*true", policy), kind


def test_招かれていない宛先と合言葉違いを区別しない():
    """
    Scenario: 招かれていない宛先と、合言葉違いを区別しない
    Given 宛先Aは招かれておらず、宛先Bは招かれている
    When Aで入ろうとする
    And Bで誤った合言葉を示して入ろうとする
    Then どちらも SIGN_IN_FAILED として同じ内容で拒まれる

    区別するのは名簿の設定と、こちらの画面の両方。どちらか一方でも
    理由を漏らすと、誰が招かれているかを外から探れる。
    """
    assert re.search(r"PreventUserExistenceErrors:\s*ENABLED", CLOUDFORMATION)

    # 画面の側も、理由を分けずに1つの文へ潰す
    assert "メールアドレスかパスワードが違います。" in ADMIN_APP
    assert "登録されていません" not in ADMIN_APP

"""合言葉を決め直す操作のうち、この文脈が担う分を確かめる。

実行:  python3 -m pytest tests/ -v

確認コードの発行・送付・照合・期限・再利用の禁止と、合言葉の置き換えそのものは
投稿者の名簿（この文脈の外にある仕組み）が行う。こちらが担うのは、名簿が返した
ものを画面がどう扱うか——違いを外へ出さないこと、使えない人へ何を伝えるか、
名簿へ送る前に止めること。

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: uc-reset-password
"""
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3]
ADMIN_APP = (SKILL / "scripts" / "app" / "app.js").read_text(encoding="utf-8")
CLOUDFORMATION = (SKILL / "infra" / "cloudformation.yaml").read_text(encoding="utf-8")


def _forgot_flow() -> str:
    """確認コードを求めるところの処理だけを取り出す。"""
    start = ADMIN_APP.index("ForgotPassword")
    return ADMIN_APP[start:ADMIN_APP.index("ConfirmForgotPassword")]


def test_招かれていない宛先でも同じ返事をする():
    """
    Scenario: 招かれていない宛先でも同じ返事をする
    Given 宛先Aは招かれておらず、宛先Bは招かれている
    When Aで確認コードを求める
    And Bで確認コードを求める
    Then どちらも同じ内容が返る
    And Aへは何も送られない
    """
    flow = _forgot_flow()

    # 送れなかった場合の分岐を作らず、失敗を飲んで同じ道へ進む
    assert re.search(r"\.catch\(function \(\) \{[^}]*\}\)", flow)
    assert ".then(function () {" in flow
    # 送れたかどうかで文言を変えていない
    assert flow.count("gateForm('resetform')") == 1


def test_招待に応じていない人は使えない():
    """
    Scenario: 招待に応じていない人は使えない
    Given ある人が招かれ、まだ一度も入っていない
    When その宛先で確認コードを求めて決め直そうとする
    Then RESET_NOT_AVAILABLE として拒まれる
    And 管理者が招き直すほかに手立てが無い

    名簿は NotAuthorized / InvalidParameter を返すだけで、それが「まだ入って
    いない人」を意味すると決めているのはこの製品の側。
    """
    assert re.search(r"NotAuthorized\|InvalidParameter", ADMIN_APP)
    assert "まだ招待に応じていません" in ADMIN_APP
    assert "招待を送り直してもらってください" in ADMIN_APP


def test_弱い合言葉は名簿へ送る前に止める():
    """
    Scenario: 弱い合言葉は名簿へ送る前に止める
    Given 正しい確認コードが届いている
    When 決められた強さを満たさない合言葉を示す
    Then 名簿へ送られる前に、その場で拒まれる
    And 出荷する設定にも同じ強さが含まれている
    """
    reset = ADMIN_APP[ADMIN_APP.index("$('resetform')"):]
    guard = reset.index("badPassword")
    sent = reset.index("ConfirmForgotPassword")
    assert guard < sent, "名簿へ送る前に止めていない"
    assert re.search(r"if \(bad\).*return", reset[:sent], re.S)

    policy = CLOUDFORMATION[CLOUDFORMATION.index("PasswordPolicy:"):][:400]
    shipped = int(re.search(r"MinimumLength:\s*(\d+)", policy).group(1))
    assert int(re.search(r"value\.length < (\d+)", ADMIN_APP).group(1)) == shipped

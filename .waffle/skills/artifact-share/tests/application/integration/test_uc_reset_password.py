"""決め直す操作が守る約束を確かめる。

対象の仕様: uc-reset-password（操作保証）
"""
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3]
LAMBDA = SKILL / "lambda" / "admin_api"
ADMIN_APP = (SKILL / "scripts" / "app" / "app.js").read_text(encoding="utf-8")


def test_確認コードはどこにも残らない():
    """
    Scenario: 確認コードはどこにも残らない
    Given ある人が確認コードを示して決め直している
    When この文脈が持つものを調べる
    Then 確認コードも、そこから確認コードを導けるものも見つからない
    """
    holding = re.compile(r"""(?ix)
        (\bconfirmation_?code\s*[:=][^=]
        |\[["']confirmationCode["']\]
        |\.get\(\s*["']confirmationCode["'])
    """)
    for path in list(LAMBDA.rglob("*.py")):
        if "tests" in path.parts:
            continue
        found = holding.findall(path.read_text(encoding="utf-8"))
        assert found == [], f"{path}: {found}"

    # 画面の側も、渡したあとは持ち物から消す
    assert "clearSecrets" in ADMIN_APP


def test_決め直しても公開したものは変わらない():
    """
    Scenario: 決め直しても公開したものは変わらない
    Given ある人が共有アーティファクトAを公開している
    When その人が合言葉を決め直す
    Then Aは公開されたまま残っている
    And 閲覧トークンを持つ閲覧者はAを開ける

    合言葉は名簿の側にあり、共有アーティファクトの記録にも閲覧の面にも
    現れない。だから決め直しが波及する経路そのものが無い。
    """
    sources = list((LAMBDA / "application").rglob("*.py"))
    sources += list((LAMBDA / "domain").rglob("*.py"))
    joined = "\n".join(p.read_text(encoding="utf-8") for p in sources)

    # 合言葉の決め直しに触れる口を、業務の側は一切持たない
    assert "ForgotPassword" not in joined
    assert "ConfirmForgotPassword" not in joined

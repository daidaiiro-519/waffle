"""閲覧トークンについて、受け入れシナリオの外側で守りたいこと。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

シナリオと1対1で対応するものは application/acceptance/ の各ファイルにある。
ここに残すのは、どのシナリオにも書かれていないが崩れると困ること——値が
一度しか手に入らないこと、招かれていない者を拒むこと、管理者の扱い。

対象の仕様:
  uc-issue-view-token（受け入れ基準のうち、シナリオを持たないもの）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

from view_token_setup import ADMIN, AID, NOW, OTHER, issue, setup  # noqa: E402
from application.view_token_access import ViewTokenError  # noqa: E402
from domain import view_token  # noqa: E402


def test_発行のときだけ値が返り記録には残らない():
    deps = setup()

    r = issue(deps, "レビュー班", ttl=view_token.WEEK)

    assert r.token
    assert r.name == "レビュー班"
    assert r.expires_at == NOW + view_token.WEEK
    assert r.token_shown_once is True
    # 記録には値そのものが残らない
    assert r.token not in str(deps.artifacts.find(AID).view_tokens)


def test_招かれていない者は発行できない():
    deps = setup()

    with pytest.raises(ViewTokenError) as x:
        issue(deps, "勝手に", caller=OTHER)

    assert x.value.code == "TARGET_NOT_FOUND"


def test_管理者は他人のものも扱える():
    deps = setup(owner="publisher-2")

    r = issue(deps, "管理者から", caller=ADMIN)

    assert r.token

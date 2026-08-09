"""利用者のブラウザで動く出荷物が、他の出荷物と食い違っていないかを確かめる。

実行:  python3 -m pytest tests/ -v

ブラウザには層が無く、業務の判断も置かない。ここで確かめるのは振る舞いではなく、
同じ規則が2箇所に写されているときに、その2つが一致していること。

写しが黙ってずれる形は、この製品が一度実際に踏んでいる——閲覧ゲートと管理APIが
同じ規則を別々に持ち、両方が同じ誤解で揃って通り、実環境で初めて現れた。
その再発防止として infra/contract/token-records.json という共通の表があり、
ここも同じ考えで書く。

対象の仕様: uc-sign-in / uc-post-comment / agg-comment（出荷物どうしの契約）
"""
import json
import re
from pathlib import Path

from conftest import SKILL

CLOUDFORMATION = (SKILL / "infra" / "cloudformation.yaml").read_text(encoding="utf-8")
ADMIN_APP = (SKILL / "scripts" / "app" / "app.js").read_text(encoding="utf-8")
VIEWER = (SKILL / "references" / "templates" / "share-wrapper.html").read_text(
    encoding="utf-8")
GATE = (SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js").read_text(
    encoding="utf-8")


def _policy(field: str) -> str:
    """出荷する利用者プールの設定から、合言葉の強さを1つ読む。"""
    block = CLOUDFORMATION[CLOUDFORMATION.index("PasswordPolicy:"):][:400]
    return re.search(rf"{field}:\s*(\S+)", block).group(1)


def test_合言葉の長さが管理画面と設定で一致する():
    """設定を強めても画面が古い基準を通すと、利用者はここで通ってから拒まれる。"""
    shipped = int(_policy("MinimumLength"))

    checked = int(re.search(r"value\.length < (\d+)", ADMIN_APP).group(1))

    assert checked == shipped


def test_合言葉に求める文字種が管理画面と設定で一致する():
    required = {kind for kind in ("Uppercase", "Lowercase", "Numbers")
                if _policy(f"Require{kind}") == "true"}
    checks = re.search(r"if \(!/\[A-Z\]/\.test.*?\) \{", ADMIN_APP, re.S).group(0)

    present = set()
    if "[A-Z]" in checks:
        present.add("Uppercase")
    if "[a-z]" in checks:
        present.add("Lowercase")
    if "[0-9]" in checks:
        present.add("Numbers")

    assert present == required


def test_管理者のグループ名が管理画面と設定で一致する():
    """名前がずれると、管理者が管理者として扱われなくなる。"""
    shipped = re.search(r"GroupName:\s*(\S+)", CLOUDFORMATION).group(1)

    assert f"'{shipped}'" in ADMIN_APP


def test_招かれていない宛先と合言葉違いを区別しない設定が出荷される():
    """区別すると、誰が招かれているかを外から探れてしまう。"""
    assert re.search(r"PreventUserExistenceErrors:\s*ENABLED", CLOUDFORMATION)


def test_管理画面は入れなかった理由を1つの文へ潰す():
    """設定だけでなく、画面の側も理由を分けて伝えないこと。"""
    assert "メールアドレスかパスワードが違います。" in ADMIN_APP
    # 「その宛先は登録されていません」の類が無いこと
    assert "登録されていません" not in ADMIN_APP


def test_閲覧画面はコメントを文字としてのみ描く():
    """agg-comment の不変条件「本文は常に文字として扱われる」を守っているのは
    描き方ただ一点。誰でも投稿でき、投稿は上書きできず残るため、ここが崩れると
    消せない仕掛けが残る。"""
    # 注釈の中の言及は数えない。実際に代入している箇所だけを見る
    assignments = re.findall(r"\.innerHTML\s*=", VIEWER)
    assert assignments == []
    assert ".textContent" in VIEWER


def test_閲覧画面は上書きを拒む宣言を必ず付けて書き込む():
    """付けずに送れると、投稿済みのコメントを書き換えられる。"""
    assert "'if-none-match': '*'" in VIEWER


def test_閲覧ゲートは上書きの宣言が無い書き込みを拒む():
    """送る側と検査する側の両方に同じ規則がある。片方だけでは守れない。"""
    assert "ifNoneMatch !== '*'" in GATE


def test_区切りかどうかを鍵で決める():
    """本文の値で決めると、閲覧者が区切りだと名乗れる。閲覧ゲートは要求の本文を
    読めないので、本文を根拠にする限り防げない。鍵なら検査できる。"""
    contract = json.loads(
        (SKILL / "infra" / "contract" / "comment-entries.json").read_text(
            encoding="utf-8"))
    marker = contract["形式"]["区切りの目印"]

    # 閲覧画面は鍵で決める（本文の kind を信じない）
    assert f"key.endsWith('{marker}')" in VIEWER
    assert "String(rec.kind" not in VIEWER
    # 閲覧ゲートは、閲覧者がその鍵で書くことを拒む
    assert f"uri.endsWith('{marker}')" in GATE
    # 業務のLambdaが書く区切りも同じ目印を使う
    repository = (SKILL / "lambda" / "admin_api" / "adapters" / "outbound"
                  / "stored_comment_repository.py").read_text(encoding="utf-8")
    assert f'DIVIDER_SUFFIX = "{marker}"' in repository

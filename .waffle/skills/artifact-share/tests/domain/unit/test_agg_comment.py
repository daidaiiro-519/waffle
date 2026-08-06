"""コメントが常に守ることを、不変条件シナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

この集約には Python のクラスが無い。コメント1件は保管の1オブジェクトで、
一貫性の境界は「1オブジェクト＝1回の書き込み」として実在する。守っているのは
閲覧画面・閲覧ゲート・保管の書き込み条件・業務のLambda の4つで、どれも
コードだが同じ言語でも同じ配布単位でもない。

だからここで確かめるのは、宣言された不変条件が、それぞれ実際にどこで
どう守られているか。守り手が消えれば落ちる形にしてある。

先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは仕様の文言を
一字一句そのまま写したもの。

対象の仕様: agg-comment（不変条件）
"""
import json
import re
from pathlib import Path

from adapters.outbound.stored_comment_repository import (
    DIVIDER_SUFFIX, StoredCommentRepository,
)
from fakes import FakeStore

SKILL = Path(__file__).resolve().parents[3]
VIEWER = (SKILL / "references" / "templates" / "share-wrapper.html").read_text(
    encoding="utf-8")
GATE = (SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js").read_text(
    encoding="utf-8")

A = "aaaaaaaa"


def test_投稿したコメントは後から変えられない():
    """
    Scenario: 投稿したコメントは後から変えられない
    Given 閲覧者が共有アーティファクトAにコメントを1件残している
    When 同じIDで別の内容のコメントを残そうとする
    Then 元のコメントは変わらない

    守っているのは保管の書き込み条件。送る側が「まだ無いときだけ書く」と
    宣言し、検査する側が宣言の無い書き込みを通さない。
    """
    assert "'if-none-match': '*'" in VIEWER
    assert "ifNoneMatch !== '*'" in GATE


def test_本文は文字として扱われる():
    """
    Scenario: 本文は文字として扱われる
    Given 閲覧者が組み立ての指示に見える文字列を本文に含めてコメントを残す
    When そのコメントが他の閲覧者に示される
    Then 本文はそのままの文字として読める
    And 指示として実行されることはない

    守っているのは描き方ただ一点。投稿は誰でもでき、上書きできず残るため、
    ここが崩れると消せない仕掛けが残る。
    """
    assert re.findall(r"\.innerHTML\s*=", VIEWER) == []
    assert ".textContent" in VIEWER
    # 読み込んだ値も、必ず文字へ寄せてから扱う
    assert re.search(r"body:\s*String\(rec\.body", VIEWER)


def test_他の共有アーティファクトのコメントへは返信できない():
    """
    Scenario: 他の共有アーティファクトのコメントへは返信できない
    Given 共有アーティファクトBにコメントが1件ある
    When 共有アーティファクトAへのコメントとして、共有アーティファクトBのコメントを返信先に指そうとする
    Then 返信として成立しない

    守っているのは保管の配置。コメントは共有アーティファクトごとの区画にだけ
    置かれ、閲覧ゲートも鍵がその区画に収まっているかを検査する。
    """
    assert "'comments/' + ARTIFACT_ID + '/'" in VIEWER
    assert re.search(r"\^/comments/'\s*\+\s*artifactId", GATE)


def test_差し替え後もコメントは残り区切りが読み取れる():
    """
    Scenario: 差し替え後もコメントは残り、区切りが読み取れる
    Given 共有アーティファクトAに2件のコメントが残っている
    When 共有アーティファクトAの中身を差し替える
    Then 2件のコメントはいずれも残っている
    And 差し替えが行われた時点が区切りとしてコメントの並びに現れる
    And その区切りより前のコメントは差し替え前のものだと読み取れる

    ここだけは業務のLambdaが守る。区切りは別の鍵として足されるだけで、
    それまでのコメントには触れない。
    """
    store = FakeStore()
    for at in (1_700_000_010, 1_700_000_020):
        store.put(f"comments/{A}/{at}-abcd1234.json",
                  json.dumps({"kind": "comment", "author": "田中", "body": "意見"},
                             ensure_ascii=False), "application/json")
    before = dict(store.objects)
    comments = StoredCommentRepository(store)

    comments.add_replacement_divider(A, 1_700_000_100)

    # それまでの2件はひとつも触られていない
    for key, value in before.items():
        assert store.objects[key] == value
    # 区切りは別の1件として、その時点の位置に足される
    keys = store.list(f"comments/{A}/")
    assert len(keys) == 3
    divider = [k for k in keys if k.endswith(DIVIDER_SUFFIX)]
    assert len(divider) == 1
    assert keys.index(divider[0]) == 2   # 2件のあとに来る
    # 数えるときは区切りを含めない（読む側が前後を区別できる）
    assert comments.count_of(A) == 2

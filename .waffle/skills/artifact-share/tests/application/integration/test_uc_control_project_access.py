"""まとめの見せ方を変える操作が守る約束を確かめる。

実行:  python3 -m pytest tests/ -v

見せ方を変えるのは、まとめの側で完結する。入っている共有アーティファクトの
中身も、そこへ個別に渡した閲覧トークンも、集まったコメントも動かない。

対象の仕様: uc-control-project-access（操作保証）
"""
import json

from project_setup import X, artifact, assign, owned, setup
from application.usecases.control_project_access import ControlProjectAccess
from application.usecases.issue_view_token import IssueViewToken
from application.usecases.revoke_view_token import RevokeViewToken
from domain.value_objects.view_subject import ViewSubject
from usecase_builder import build

AID = "aaaaaaaa"


def _comment(deps, artifact_id, at, author, body):
    """閲覧者が書き込んだ1件。閲覧画面が書くのと同じ形。"""
    deps.store.put(
        f"comments/{artifact_id}/{at}-abcd1234.json",
        json.dumps({"kind": "comment", "author": author, "decision": "comment",
                    "body": body, "parentId": None,
                    "postedAt": "2026-07-01T10:00:00Z"}, ensure_ascii=False),
        "application/json")


def test_見せ方を変えても中身とコメントは動かない():
    """
    Scenario: 見せ方を変えても中身とコメントは動かない
    Given Aにコメントが3件付いている
    When プロジェクトの閲覧トークンを1本無効にして、新しく1本発行する
    And プロジェクトを公開停止して再開する
    Then Aの中身は変わっていない
    And Aの個別の閲覧トークンは変わっていない
    And Aのコメントは3件のまま残っている
    """
    deps = setup()
    p = owned(deps, caller=X)
    artifact(deps, AID, "検索基盤の選定")
    assign(deps, X, AID, p.project_id)
    deps.store.put(f"p/{AID}/content.html", "<html>中身</html>", "text/html")
    build(deps, IssueViewToken).run(X, ViewSubject.artifact(AID), "別の相手", None)
    for at, author in ((1, "田中"), (2, "佐藤"), (3, "山田")):
        _comment(deps, AID, at, author, "意見")

    content_before = deps.store.get(f"p/{AID}/content.html")
    token_before = deps.keys.written[f"token:{AID}"]
    comments_before = deps.store.list(f"comments/{AID}/")
    assert len(comments_before) == 3

    project = ViewSubject.project(p.project_id)
    issued = build(deps, IssueViewToken).run(X, project, "レビュー班", None)
    build(deps, RevokeViewToken).run(X, project, issued.token_id)
    build(deps, IssueViewToken).run(X, project, "定例レビュー", None)
    build(deps, ControlProjectAccess).run("suspend", X, p.project_id)
    build(deps, ControlProjectAccess).run("resume", X, p.project_id)

    assert deps.store.get(f"p/{AID}/content.html") == content_before
    assert deps.keys.written[f"token:{AID}"] == token_before
    assert deps.store.list(f"comments/{AID}/") == comments_before

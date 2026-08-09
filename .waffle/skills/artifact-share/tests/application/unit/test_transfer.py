"""引き継ぎと、管理者が扱える範囲を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

対象の仕様: uc-transfer-artifact、および uc-suspend-artifact /
uc-resume-artifact / uc-reissue-view-token / uc-replace-content の
「誰が扱えるか」の受け入れ基準。
"""



from usecase_builder import build  # noqa: E402
from application.usecases.list_my_artifacts import ListMyArtifacts  # noqa: E402
from application.usecases.transfer_artifact import TransferArtifact  # noqa: E402



from transfer_setup import ADMIN, X, Y, setup  # noqa: E402


# ── 管理者が扱える範囲 ──────────────────────────────────

def test_一覧には誰が公開したかが分かる():
    """管理者が全員のものを見るとき、持ち主が読めないと引き継ぎ先を決められない"""
    deps, r = setup()
    assert build(deps, ListMyArtifacts).run(ADMIN).artifacts[0].uploaded_by == X.id


# ── 引き継ぎ ────────────────────────────────────────────

def test_引き継いでもコメントの並びに区切りは増えない():
    deps, r = setup()
    build(deps, TransferArtifact).run(ADMIN, r.artifact_id, Y.id)
    assert deps.store.list(f"comments/{r.artifact_id}/") == []

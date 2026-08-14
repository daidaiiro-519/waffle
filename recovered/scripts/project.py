"""プロジェクト。

複数の共有アーティファクトをまとめて見せるための単位。1つの閲覧トークンで、
入っているものをまとめて開いてもらう。

入っているものの一覧はここが持たない。所属の正は共有アーティファクトの側に
あり、こちらの一覧は閲覧者へ見せるために組み立て直せる投影である。両側が正だと、
食い違ったときにどちらを信じてよいか誰にも言えなくなる。

対象の仕様: agg-project
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from domain.value_objects.project import (
    PUBLISHED, SUSPENDED, ProjectId, ProjectKey, ProjectOwner, ProjectScope, ProjectStatus,
)
from domain.value_objects.view_token import ProjectViewToken, ViewTokenExpiry


@dataclass(frozen=True)
class Project:
    """まとめて見せるための単位1つ。"""

    project_id: ProjectId
    display_name: str
    project_key: ProjectKey
    status: ProjectStatus
    owner: ProjectOwner
    scope: ProjectScope
    created_at: int
    view_tokens: tuple[ProjectViewToken, ...] = ()
    updated_at: int = 0

    # ── 誰が扱ってよいか ──────────────────────────────

    def manageable_by(self, caller_id: str, is_admin: bool = False) -> bool:
        """見せ方を変えてよいか。持ち主か管理者だけ。"""
        return is_admin or self.owner.value == caller_id

    def accepts_membership_from(self, caller_id: str, is_admin: bool = False) -> bool:
        """共有アーティファクトを出し入れしてよいか。

        見せ方を変える判定と違い、こちらは共有の別を見る——共有なら招かれた
        投稿者なら誰でも自分のものを入れられる。
        """
        return self.manageable_by(caller_id, is_admin) or self.scope.is_shared()

    # ── 閲覧トークンに許すこと ────────────────────────

    def accepts_expiry(self, expiry: ViewTokenExpiry, now: int) -> bool:
        """その期限で閲覧トークンを発行してよいかを判じる。

        置いておく場なので、期限を設けないことも選べる。共有アーティファクト
        1件と違い、まとめは渡したあとも使われ続けることが前提にある。

        Args:
            expiry: 与えようとしている期限。
            now: 発行しようとしている時点。

        Returns:
            与えてよければ True。まとめはどの期限も受け入れる。

        Raises:
            なし。
        """
        return True

    # ── 状態を変える ──────────────────────────────────

    def suspended(self, at: int) -> "Project":
        """このプロジェクトの閲覧トークンでは何も開けない状態にする。

        入っている共有アーティファクトは、それぞれの閲覧トークンで引き続き
        開ける。まとめは見せ方の束ねであって、入れ物ではない。
        """
        return replace(self, status=ProjectStatus(SUSPENDED), updated_at=at)

    def resumed(self, at: int) -> "Project":
        """再び開ける状態に戻す。閲覧トークンはそのまま。"""
        return replace(self, status=ProjectStatus(PUBLISHED), updated_at=at)

    def with_view_tokens(self, tokens: tuple[ProjectViewToken, ...], at: int) -> "Project":
        """閲覧トークンの顔ぶれを置き換える。"""
        return replace(self, view_tokens=tuple(tokens), updated_at=at)

"""公開の状態と、公開できる範囲の決まり。

ここにあるのは判断だけで、判断した結果をどう伝えるか（どのエラーコードで
拒むか）は呼び出し側が決める。domain は誰に向けて答えるかを知らないため。

対象の仕様: agg-shared-artifact / agg-project / uc-assign-to-project
"""
from __future__ import annotations

# 公開の状態。閲覧の面もこの語をそのまま読む
ACTIVE = "active"
DISABLED = "disabled"

# 受け取るHTMLの上限。これを超えるものは、署名付きの経路で直接受け渡す設計へ移す
MAX_CONTENT_BYTES = 5 * 1024 * 1024

# 1つの共有アーティファクトが入れるプロジェクトの数
MAX_PROJECTS_PER_ARTIFACT = 3

# 誰が共有アーティファクトを出し入れできるか
PERSONAL = "PERSONAL"      # 持ち主だけ
SHARED = "SHARED"          # 招かれた投稿者なら誰でも、自分のものを
SCOPES = (PERSONAL, SHARED)


def is_published(meta: dict) -> bool:
    """いま開ける状態か。"""
    return meta.get("status") == ACTIVE


def is_suspended(meta: dict) -> bool:
    """公開が止まっているか。"""
    return meta.get("status") == DISABLED


def within_project_limit(projects: list[str]) -> bool:
    """入れているプロジェクトの数が上限に収まっているか。"""
    return len(projects) <= MAX_PROJECTS_PER_ARTIFACT


def is_known_scope(scope: str) -> bool:
    """出し入れの範囲として認めている値か。"""
    return scope in SCOPES

"""共有アーティファクトとプロジェクトを指す識別子。

どちらも人が読み上げ、書き写し、口頭で伝えることがある。読み間違えやすい文字
（l と 1、o と 0）を字種から外してあるのはそのため。連番にしないのは、
識別子から他人のものを数え上げられないようにするため。

対象の仕様: agg-shared-artifact / agg-project
"""
from __future__ import annotations

import secrets

# 読み間違えやすい文字（l, o, 0, 1）を外した英数字
ID_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"

ARTIFACT_ID_LENGTH = 8
PROJECT_ID_LENGTH = 6


def new_artifact_id() -> str:
    """共有アーティファクトを1つ指す識別子を発行する。"""
    return random_chars(ARTIFACT_ID_LENGTH)


def new_project_id() -> str:
    """プロジェクトを1つ指す識別子を発行する。"""
    return random_chars(PROJECT_ID_LENGTH)


def random_chars(length: int) -> str:
    """読み間違えにくい字種から、推測できない並びを作る。"""
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(length))

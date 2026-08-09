"""共有アーティファクトとプロジェクトを指す識別子が、常に満たす形。

どちらも人が読み上げ、書き写し、口頭で伝えることがある。読み間違えやすい文字
（l と 1、o と 0）を字種から外してあるのはそのため。連番にしないのは、識別子
から他人のものを数え上げられないようにするため。

字種と桁数はこの層が正本として持つ。作る手立て（推測できない並びをどう得るか）
は実行環境に結びつくので外の口が担うが、どんな形なら識別子として通るかを決める
のはここである。作る側に正本を置くと、その経路を通らない値が素通りする。

対象の仕様: agg-shared-artifact / agg-project
"""
from __future__ import annotations

# 読み間違えやすい文字（l, o, 0, 1）を外した英数字
ID_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"

ARTIFACT_ID_LENGTH = 8
PROJECT_ID_LENGTH = 6


class MalformedIdentifier(ValueError):
    """識別子として通らない形を渡された。"""


def ensure(value: str, length: int, what: str) -> None:
    """識別子として通る形かを確かめ、通らなければ拒む。

    Args:
        value: 確かめる値。
        length: その識別子に定めた桁数。
        what: 拒むときに何の識別子かを伝えるための名前。

    Returns:
        なし。

    Raises:
        MalformedIdentifier: 桁数が違う、または字種の外の文字を含む。
    """
    if len(value) != length or any(c not in ID_ALPHABET for c in value):
        raise MalformedIdentifier(f"{what} として通らない形です: {value!r}")

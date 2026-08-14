"""操作している人。

誰であるかと、管理者かどうかだけを持つ。どうやって本人だと確かめたか
（証明の仕組み）はここに現れない——確かめ終えた結果だけを受け取る。

業務の語彙ではなくこの層に置くのは、管理者という区分を決めているのがこの文脈
ではなく招かれている人の名簿（外の仕組み）だからである。その語彙に依る値を
最も内側の層へ置くと、内側から外のモデルへ向かう依存が生まれる。名簿の語彙を
自分の言葉へ移し替える口のすぐ内側が、依存の届く範囲を最も狭く保てる。

書き換えられない形にしてあるのは、扱ってよいかを判じたあとで管理者かどうかを
差し替える経路を残さないため。

対象の仕様: uc-sign-in / uc-list-publishers / uc-invite-publisher
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Caller:
    """操作している人。誰であるかと、管理者かどうかだけを持つ。"""

    id: str
    is_admin: bool = False

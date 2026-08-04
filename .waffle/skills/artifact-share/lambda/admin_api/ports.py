"""application が外部へ要求する口。

同じ名前の Deps が publish.py と manage.py に別々にあり、片方だけを直しても
もう片方が気づけない状態だった。外部との接点は1箇所で宣言する。

ここに置くのは「何を必要としているか」であって、どう実現するかではない。
実物の組み立ては合成ルート（main.py）が行う。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Caller:
    """操作している人。誰であるかと、管理者かどうかだけを持つ。"""

    id: str
    is_admin: bool = False


@dataclass
class Deps:
    """外部との接点。

    store             保管の読み書き（put/get/list）。削除は持たない
    keys              閲覧トークンの保管の読み書き（put/get）
    now               現在時刻（エポック秒）。検証で固定できるようにする
    viewer_domain     閲覧の面の配信ドメイン。共有URLの組み立てに使う
    identify          利用者の証明から、その人を表す値を返す。招かれていなければ None
    directory         招かれている人の名簿（find/invite/remove）。この文脈の外にある
    wrapper_template  閲覧画面の雛形。{{アーティファクトID}} を置き換えて配置する
    project_page      プロジェクトの一覧ページの雛形。どのプロジェクトにも同じものを置く
    """

    store: object
    keys: object
    now: Callable[[], int] = lambda: int(time.time())
    viewer_domain: str = ""
    identify: object = None
    directory: object = None
    wrapper_template: str = ""
    project_page: str = ""

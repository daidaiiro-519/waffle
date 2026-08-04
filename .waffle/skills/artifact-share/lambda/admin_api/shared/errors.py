"""操作が失敗したことを、識別できるコードとともに伝える。

コードを必ず伴わせるのは、受け口が「何が起きたか」で答えを変えるため。
文言だけでは分岐できず、文言を変えた瞬間に分岐が壊れる。

種別（公開・管理・プロジェクト・投稿者の名簿）ごとに派生を持つのは、受け口が
同じコードでも種別によって違う答え方をするため。中身は同じなので、ここに1つ
だけ置く。
"""
from __future__ import annotations


class ApplicationError(Exception):
    """業務上の理由で操作を続けられないこと。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class PublishError(ApplicationError):
    """公開できない。"""


class ManageError(ApplicationError):
    """公開したものを手入れできない。"""


class ProjectError(ApplicationError):
    """プロジェクトを扱えない。"""


class PublisherError(ApplicationError):
    """招かれている人の名簿を扱えない。"""

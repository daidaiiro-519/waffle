"""application が外部へ要求する口。

architecture が「application が要求する driven インターフェース（Protocol）。
構造体のフィールドとして持たず、型として宣言する」と定めているため、
依存をひとまとめの構造体にせず、能力ごとに型を分ける。

こうすると、ある操作が何を必要としているかが引数の型から読める。
まとめて渡す形だと、使わないものまで含めて全員に配ることになり、
どの操作が何に依存しているかが型から失われる。

名前は業務の言葉で付ける。ArtifactStore は「共有アーティファクトの保管」であって
「S3 のクライアント」ではない。何で実現するかは adapter 側の関心事。
"""
from __future__ import annotations

from typing import Protocol

from domain.caller import Caller  # noqa: F401






class PublisherDirectory(Protocol):
    """招かれている人の名簿。この文脈の外にある仕組み。"""

    def find(self, email: str) -> dict | None:
        """その宛先で招かれている人を探す。居なければ None。"""
        ...

    def list(self) -> list[dict]:
        """招かれている人を列挙する。"""
        ...

    def admins(self) -> list[dict]:
        """管理者を列挙する。"""
        ...

    def invite(self, email: str) -> dict:
        """その宛先の人を招く。"""
        ...

    def resend(self, email: str) -> None:
        """招きを送り直す。"""
        ...

    def remove(self, email: str) -> None:
        """その人を名簿から外す。"""
        ...


class PublisherIdentifier(Protocol):
    """利用者の証明から、その人を表す値を返す。招かれていなければ None。"""

    def __call__(self, authorization: str) -> str | None:
        ...


class Clock(Protocol):
    """現在時刻（エポック秒）。検証で固定できるようにするために口として持つ。"""

    def __call__(self) -> int:
        ...

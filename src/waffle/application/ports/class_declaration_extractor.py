"""class declaration extractor — ソースコードからクラス定義名・フィールド名を
機械的に抽出するport。

check_usecase_class_drift/check_aggregate_class_driftが、宣言された名前と
実装クラスの対応関係を検証するために使う。実装（Python標準ライブラリのast、
tree-sitter等）はadapter側の責務。コアはこの抽象にのみ依存し、対象言語の
構文解析技術を知らない（architecture-port-adapter原則）。
"""
from __future__ import annotations

from typing import Protocol


class ClassDeclarationExtractor(Protocol):
    def class_names(self, source: str, language: str) -> list[str]:
        """sourceに定義されている全クラス名を、出現順で返す。"""
        ...

    def field_names(self, source: str, language: str, class_name: str) -> list[str]:
        """class_nameという名前のクラス本体直下にあるフィールド宣言の名前を、
        出現順で返す。該当クラスが無ければ空リスト。"""
        ...

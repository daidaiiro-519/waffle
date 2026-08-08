"""ImportExtractor port — ソースコードが宣言している依存（他のモジュールへの参照）を
取り出す Secondary Port。

言語ごとに依存の書き方は全く違う（Pythonはドット区切り、TypeScriptは相対パス、
Goはモジュールパス、Rustは :: 区切り）。この差はアダプタが吸収し、コアには
「参照文字列の一覧」という言語非依存の形だけを返す。
"""
from __future__ import annotations

from typing import Protocol


class UnsupportedLanguage(Exception):
    """アダプタが対応していない言語が指定されたときに送出する。"""


class ImportExtractor(Protocol):
    """ソースが宣言している依存を取り出す。"""
    def imports(self, source: str, language: str) -> list[str]:
        """source が宣言している依存の参照を、出現順で返す。

        返すのは書かれたままの参照（例: waffle.domain.x / ../domain/x /
        example.com/app/domain）であり、実在するファイルへの解決は行わない。
        どのファイルを指すかは置き場所の宣言と実在に依存する判断であり、
        構文解析の責務ではないため。

        構文解析できなければ SyntaxError、対応していない言語なら
        UnsupportedLanguage を送出する。
        """
        ...

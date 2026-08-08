"""test function extractor — テストコードから、テストの名前と文書コメントを
機械的に抽出するport。

check_scenario_driftが、specのシナリオとテストの対応関係を検証するために使う。
実装（tree-sitter等）はadapter側の責務。コアはこの抽象にのみ依存し、対象言語の
構文解析技術を知らない（architecture-port-adapter原則）。

言語ごとに違うものが3つあり、いずれもadapterが吸収する:

- テストを表すもの（関数定義／メソッド宣言／関数呼び出し）
- 名前の在り処（関数名／メソッド名／文字列引数）
- 文書コメントの位置（関数の内側／関数の直前）

飾り（三重引用符・ブロックコメントの記号・行頭のアスタリスク・行コメント記号）を
落とすのもadapterの責務。落とし方が言語ごとに違うため、コアへ持ち込むと
言語の知識がコアへ戻ってくる。
"""
from __future__ import annotations

from typing import Protocol


class UnsupportedLanguage(Exception):
    """アダプタが対応していない言語が指定されたときに送出する。"""


class TestFunctionExtractor(Protocol):
    """テストの名前と文書コメントを取り出す。"""
    def test_functions(self, source: str, language: str) -> list[dict]:
        """sourceに含まれるテストを、出現順で返す。

        各要素は name（テストの名前）と doc（飾りを落とした文書コメント。
        無ければ空文字）を持つ。構文解析できなければ SyntaxError を送出する。
        """
        ...

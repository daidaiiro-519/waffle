"""surface_extractor — 受け口のソースから、外へ差し出されている入口を取り出すport。

入口の見え方は口ごとに違う。命令行は選択肢として、道具呼び出しは関数の引数として、
要求本文はキーとして入力を受け取る。取り出し方だけが違って、突き合わせたい中身
（どの操作の入口か・どんな入力を受けるか）は同じなので、取り出しをここへ寄せる。

どの操作の入口かは、この層では決めない。入口が参照している名前をそのまま返し、
宣言された操作名と突き合わせるのは呼び出し側の仕事にする。ここで判断すると、
言語ごとのadapterが業務の語彙を知ることになる。
"""
from __future__ import annotations

from typing import Protocol


class UnsupportedLanguage(Exception):
    """対応するadapterを持たない言語を渡されたときに送出する。"""


class SurfaceExtractor(Protocol):
    """受け口のソースから入口を取り出す。"""

    def surfaces(self, source: str, language: str) -> list[dict]:
        """ソースに含まれる入口を列挙する。

        Args:
            source: 受け口のソースコード。
            language: そのソースの言語。

        Returns:
            入口ごとに {name, params, references} を持つ辞書の並び。
            params は受け取る入力の名前、references はその入口が参照している名前。

        Raises:
            UnsupportedLanguage: 対応するadapterを持たない言語。
        """
        ...

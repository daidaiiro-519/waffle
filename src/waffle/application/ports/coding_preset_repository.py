"""CodingPresetRepository port — CodingSchemaプリセット解決の Secondary Port。

プリセットは、新しいプロダクトの規約4文書の出発点になる。読むだけでなく書き戻せる
のは、実践で確かめた規約を次の出発点へ育てるため（uc-update-coding-preset）。
"""
from __future__ import annotations

from typing import Protocol


class CodingPresetRepository(Protocol):
    """規約のプリセットを読み書きする。"""
    def load(self, preset_name: str) -> dict:
        """preset_name（例: python-hexagonal）に対応する、tech-stack/architecture/
        coding-standard/test-standardの4kind分のcontentを持つプリセットをdictで返す。
        見つからなければ FileNotFoundError。"""
        ...

    def list_names(self) -> list[str]:
        """利用可能なプリセット名の一覧（昇順）を返す。"""
        ...

    def save(self, preset_name: str, preset: dict) -> None:
        """preset_name に対応するプリセットを、渡された内容で置き換える。

        書き込み先はソースツリー上のプリセット。インストール済みパッケージの
        中身を書き換える用途は想定しない。
        """
        ...

"""CodingPresetRepository port — CodingSchemaプリセット(種データ)解決の Secondary Port。"""
from __future__ import annotations

from typing import Protocol


class CodingPresetRepository(Protocol):
    def load(self, preset_name: str) -> dict:
        """preset_name（例: python-hexagonal）に対応する、tech-stack/architecture/
        coding-standard/test-standardの4kind分のcontentを持つプリセットをdictで返す。
        見つからなければ FileNotFoundError。"""
        ...

    def list_names(self) -> list[str]:
        """利用可能なプリセット名の一覧（昇順）を返す。"""
        ...

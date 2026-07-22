"""CodingPreset 解決 adapter（CodingPresetRepository 実装）。

プリセットはパッケージ内 `waffle/domain/model/CodingPresets/` に閉じる（schemaと同じ配布経路）。
importlib.resources でパッケージから解決する（インストール後も動く）。
"""
from __future__ import annotations

import json
from importlib import resources

from waffle.application.ports.coding_preset_repository import CodingPresetRepository

_PACKAGE = "waffle.domain.model"
_DIR = "CodingPresets"


class PackageCodingPresetRepository(CodingPresetRepository):
    def load(self, preset_name: str) -> dict:
        ref = resources.files(_PACKAGE) / _DIR / f"{preset_name}.json"
        text = ref.read_text(encoding="utf-8")
        return json.loads(text)

    def list_names(self) -> list[str]:
        names: list[str] = []
        ref = resources.files(_PACKAGE) / _DIR
        for child in ref.iterdir():
            if child.name.endswith(".json"):
                names.append(child.name.removesuffix(".json"))
        return sorted(names)

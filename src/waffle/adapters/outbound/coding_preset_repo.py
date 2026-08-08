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
    """プリセットの読み書きを、パッケージに同梱したファイルの上で行う。"""
    def load(self, preset_name: str) -> dict:
        """1つのプリセットを読む。

        Args:
            preset_name: 読むプリセットの名前。

        Returns:
            そのプリセットの中身。

        Raises:
            FileNotFoundError: そのプリセットが無い。
        """
        ref = resources.files(_PACKAGE) / _DIR / f"{preset_name}.json"
        text = ref.read_text(encoding="utf-8")
        return json.loads(text)

    def save(self, preset_name: str, preset: dict) -> None:
        """1つのプリセットを残す。

        Args:
            preset_name: 残すプリセットの名前。
            preset: 残す中身。

        Returns:
            なし。

        Raises:
            なし。
        """
        ref = resources.files(_PACKAGE) / _DIR / f"{preset_name}.json"
        # 既存のプリセットと同じ体裁で書き戻す（差分が体裁の違いで埋もれないように）
        text = json.dumps(preset, indent=2, ensure_ascii=False) + "\n"
        with resources.as_file(ref) as path:
            path.write_text(text, encoding="utf-8")

    def list_names(self) -> list[str]:
        """同梱しているプリセットの名前を並べる。

        Returns:
            プリセットの名前の一覧。

        Raises:
            なし。
        """
        names: list[str] = []
        ref = resources.files(_PACKAGE) / _DIR
        for child in ref.iterdir():
            if child.name.endswith(".json"):
                names.append(child.name.removesuffix(".json"))
        return sorted(names)

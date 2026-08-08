"""schema 解決 adapter（SchemaRepository 実装）。

schema はパッケージ内3箇所に閉じる（ユーザープロジェクトに配布しない）:
- `waffle/domain/model/`         Documentのschemaが指しうる型＝集約（identity持ち）
- `waffle/domain/value_objects/` 他schemaに埋め込まれる値オブジェクトの型定義（集約ではない）
- `waffle/application/dto/`      usecaseの出力データの形状定義（業務ロジックではなくusecaseの
  入出力契約なのでapplication層。集約でも値オブジェクトでもない）
importlib.resources でパッケージから解決する（インストール後も動く）。
"""
from __future__ import annotations

import json
from importlib import resources

from waffle.application.ports.schema_repository import SchemaRepository

_PACKAGES = ["waffle.domain.model", "waffle.domain.value_objects", "waffle.application.dto"]

class PackageSchemaRepository(SchemaRepository):
    """schemaの解決を、パッケージに同梱したファイルの上で行う。"""
    def load(self, schema_ref: str) -> dict:
        # schema_ref 例: "SkillSchema/v1" -> waffle/domain/model/SkillSchema/v1.json
        """1つのschemaを読む。

        Args:
            schema_ref: 読むschemaを指す参照。

        Returns:
            そのschemaの中身。

        Raises:
            FileNotFoundError: そのschemaが無い。
        """
        *dirs, name = schema_ref.split("/")
        last_error: FileNotFoundError | None = None
        for package in _PACKAGES:
            ref = resources.files(package)
            for d in dirs:
                ref = ref / d
            try:
                text = (ref / f"{name}.json").read_text(encoding="utf-8")
            except FileNotFoundError as e:
                last_error = e
                continue
            return json.loads(text)
        raise last_error

    def list_versions(self, name: str) -> list[str]:
        """その名前のschemaが持つ版を並べる。

        Args:
            name: 版を数える対象のschemaの名前。

        Returns:
            版の一覧。

        Raises:
            なし。
        """
        versions: list[str] = []
        for package in _PACKAGES:
            ref = resources.files(package) / name
            if not ref.is_dir():
                continue
            for child in ref.iterdir():
                if child.name.endswith(".json"):
                    versions.append(child.name.removesuffix(".json"))
        return versions

    def list_names(self) -> list[str]:
        """同梱しているschemaの名前を並べる。

        Returns:
            schemaの名前の一覧。

        Raises:
            なし。
        """
        names: list[str] = []
        for package in _PACKAGES:
            for child in resources.files(package).iterdir():
                if child.is_dir() and not child.name.startswith("_") and child.name not in names:
                    names.append(child.name)
        return sorted(names)

    def resolve_path(self, schema_ref: str) -> str:
        """参照から、そのschemaの実際の置き場所を求める。

        Args:
            schema_ref: 解決する参照。

        Returns:
            そのschemaの置き場所。

        Raises:
            なし。
        """
        *dirs, name = schema_ref.split("/")
        for package in _PACKAGES:
            ref = resources.files(package)
            for d in dirs:
                ref = ref / d
            candidate = ref / f"{name}.json"
            if candidate.is_file():
                return str(candidate)
        raise FileNotFoundError(schema_ref)

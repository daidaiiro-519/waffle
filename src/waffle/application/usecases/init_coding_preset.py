"""init coding preset — CodingSchemaのプリセット(種データ)から、プロダクト固有の
tech-stack/architecture/coding-standard/test-standard 4documentを一括生成する。

Harness原則: プリセットは「値」が既に決まった種データであり、AIによる値生成は行わない。
既存のscaffold createとは責務が異なる（1document骨格生成 vs 複数documentの複製）ため、
別usecaseとして切り出す。
"""
from __future__ import annotations

import json

from waffle.application.ports.coding_preset_repository import CodingPresetRepository
from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.ports.schema_repository import SchemaRepository
from waffle.domain.services.schema_versioning import latest_version
from waffle.shared.result import Err, Ok, Result

_SCHEMA_NAME = "CodingSchema"
_KINDS = ("tech-stack", "architecture", "coding-standard", "test-standard")
_TAGS_BY_KIND = {
    "tech-stack": ["tier:backend"],
    "architecture": ["tier:backend"],
    "coding-standard": ["tier:backend"],
    "test-standard": ["tier:backend"],
}


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class InitCodingPreset:
    """プリセットから、プロダクト固有の規約一式を作る。"""
    def __init__(self, documents: DocumentRepository, presets: CodingPresetRepository,
                 schemas: SchemaRepository) -> None:
        self._documents = documents
        self._presets = presets
        self._schemas = schemas

    def _latest_schema_ref(self) -> str:
        """作られる規約が指す版を、いまある版から決める。

        版をここに書き留めると、schemaが1つ上がった瞬間から古い版を指し続け、
        作られた規約が最初から検証を通らなくなる（実際にそうなっていた）。
        """
        latest = latest_version(self._schemas.list_versions(_SCHEMA_NAME))
        return f"{_SCHEMA_NAME}/{latest}" if latest else _SCHEMA_NAME

    def run(self, preset_name: str, product_name: str) -> Result[dict]:
        """プリセットから、プロダクト固有の規約一式を作る。

        Args:
            preset_name: 対象とするプリセットの名前。
            product_name: 新しく作るプロダクトの名前。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        if not preset_name or not product_name:
            return _err("MISSING_PARAM", "preset_name, product_name が必要です")
        try:
            preset = self._presets.load(preset_name)
        except FileNotFoundError:
            return _err("PRESET_NOT_FOUND", f"プリセットが見つかりません: {preset_name}")

        schema_ref = self._latest_schema_ref()
        created: list[str] = []
        skipped: list[str] = []
        for kind in _KINDS:
            document_id = f"{kind}-{product_name}"
            path = f".waffle/documents/coding/{document_id}.json"
            if self._exists(path):
                skipped.append(path)
                continue
            content = self._materialize_content(preset[kind], document_id)
            document = {
                "documentId": document_id,
                "documentType": "Coding",
                "schemaRef": schema_ref,
                "codingKind": kind,
                "stack": preset_name,
                "status": "ACTIVE",
                "tags": _TAGS_BY_KIND[kind],
                "content": content,
            }
            self._documents.save(path, document)
            created.append(path)
        return Ok({"created": created, "skipped": skipped})

    def _exists(self, path: str) -> bool:
        try:
            self._documents.load(path)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def _materialize_content(self, preset_content: dict, document_id: str) -> dict:
        content = dict(preset_content)
        title_block = dict(content["title"])
        title_block["title"] = f"{title_block['title']}：{document_id}"
        content["title"] = title_block
        return content

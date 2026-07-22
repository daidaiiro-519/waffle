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
from waffle.shared.result import Err, Ok, Result

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
    def __init__(self, documents: DocumentRepository, presets: CodingPresetRepository) -> None:
        self._documents = documents
        self._presets = presets

    def run(self, preset_name: str, product_name: str) -> Result[dict]:
        if not preset_name or not product_name:
            return _err("MISSING_PARAM", "preset_name, product_name が必要です")
        try:
            preset = self._presets.load(preset_name)
        except FileNotFoundError:
            return _err("PRESET_NOT_FOUND", f"プリセットが見つかりません: {preset_name}")

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
                "schemaRef": "CodingSchema/v4",
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

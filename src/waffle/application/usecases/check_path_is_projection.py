"""check path is projection — 実体パスがdocument.json（原本）からの投影
（render出力）かどうかを機械的に判定する application use case。

symlink解決（実体パスの取得）はファイルシステムAPIを直接知る技術的詳細であり、
呼び出し側（駆動アダプター）の責務としてusecaseの外に置く。usecaseは既に
解決済みの実体パス文字列のみを受け取り、.waffle/config.jsonの
canonicalPathTemplatesへの逆マッチという業務判断だけを行う。
"""
from __future__ import annotations

import json

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services import path_template
from waffle.shared.result import Ok, Result

_NOT_PROJECTION = {"isProjection": False, "documentKind": None, "documentId": None}


class CheckPathIsProjection:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, resolved_path: str) -> Result[dict]:
        try:
            raw = self._documents.read_text(".waffle/config.json")
            config = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return Ok(dict(_NOT_PROJECTION))

        for kind, template in config.get("canonicalPathTemplates", {}).items():
            match = path_template.reverse_parse(template, resolved_path)
            if match and "documentId" in match:
                return Ok({"isProjection": True, "documentKind": kind, "documentId": match["documentId"]})

        return Ok(dict(_NOT_PROJECTION))

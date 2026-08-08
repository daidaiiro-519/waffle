"""check path is projection — 実体パスがdocument.json（原本）からの投影
（render出力）かどうかを機械的に判定する application use case。

symlink解決（実体パスの取得）はファイルシステムAPIを直接知る技術的詳細であり、
呼び出し側（駆動アダプター）の責務としてusecaseの外に置く。usecaseは既に
解決済みの実体パス文字列のみを受け取り、schemaの読み出しとResultへの包装だけを
担う。canonicalテンプレートの収集と逆マッチという業務判断は
domain/services/deploy_target_resolution が持ち、uc-render-document の
所有権判定と同じロジックを共有する。

canonicalパスの真実源はschemaのx-render-target.pathである。config.jsonは
配置先（投影先）だけを持ち、canonicalパスは持たない。
"""
from __future__ import annotations

from waffle.application.ports.schema_repository import SchemaRepository
from waffle.domain.services import deploy_target_resolution
from waffle.shared.result import Ok, Result

_NOT_PROJECTION = {"isProjection": False, "documentKind": None, "documentId": None}


class CheckPathIsProjection:
    """その実体パスが、documentからの投影かどうかを判じる。"""
    def __init__(self, schemas: SchemaRepository) -> None:
        self._schemas = schemas

    def run(self, resolved_path: str) -> Result[dict]:
        """その実体パスが、documentからの投影かどうかを判じる。

        Args:
            resolved_path: 判定対象の実体パス（symlinkを解決した後のもの）。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        found = deploy_target_resolution.find_projection(
            deploy_target_resolution.canonical_templates(self._load_all()), resolved_path,
        )
        if found is None:
            return Ok(dict(_NOT_PROJECTION))
        document_kind, document_id = found
        return Ok({"isProjection": True, "documentKind": document_kind, "documentId": document_id})

    def _load_all(self) -> list[dict]:
        loaded: list[dict] = []
        for name in self._schemas.list_names():
            for version in self._schemas.list_versions(name):
                try:
                    loaded.append(self._schemas.load(f"{name}/{version}"))
                except (FileNotFoundError, ValueError):
                    continue
        return loaded

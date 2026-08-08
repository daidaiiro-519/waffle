"""schema_ref_guard — agg-document(Document集約)の不変条件「schemaRefを持たない
Documentへの操作はMISSING_SCHEMA_REFとして拒否される」を守る純粋なドメインサービス。
既にロード済みのDocumentの中身を見るだけで判定でき、port・実I/Oを一切必要としない。
"""
from __future__ import annotations

from waffle.shared.result import Err, Ok, Result


def require_schema_ref(document: dict) -> Result[str]:
    """document が schemaRef を持つことを確認する(MISSING_SCHEMA_REF)。

    Args:
        document: 確認する対象のdocument。

    Returns:
        schemaRefを持つOk、または MISSING_SCHEMA_REF を表すErr。

    Raises:
        なし。失敗は結果型で返す。
    """
    schema_ref = document.get("schemaRef")
    if not schema_ref:
        return Err("document に schemaRef がありません", ["MISSING_SCHEMA_REF"])
    return Ok(schema_ref)

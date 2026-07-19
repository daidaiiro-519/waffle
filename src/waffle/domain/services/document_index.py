"""document_index — Documentのcontent×schemaから索引（blockType/prompt）を動的算出する
純粋なドメインサービス。_index系操作（uc-query-documentのindex_scan、
uc-query-document-collectionのindex_scan_documents）が共通で使う。索引自体は保存せず、
読み取り時に毎回schemaのx-prompt-queryから算出する（正典はdocument.jsonのまま）。
"""
from __future__ import annotations


def build_block_index(doc: dict, schema: dict) -> dict:
    """blockType × schema.x-prompt-query から索引を読み取り時に動的算出する（保存はしない）。"""
    defs = schema.get("$defs", {})
    out: dict[str, dict] = {}
    for key, block in doc.get("content", {}).items():
        bt = block.get("blockType") if isinstance(block, dict) else None
        out[key] = {"blockType": bt, "prompt": defs.get(f"{bt}Block", {}).get("x-prompt-query")}
    return out

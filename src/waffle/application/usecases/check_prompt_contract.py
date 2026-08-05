"""check prompt contract — Schemaが定める2つの指示が、然るべき場所に然るべき名前で
置かれているかを検証する application use case。

実行/意味理解はしない（キーの有無と名前の機械的な突き合わせのみ）。指示の中身が
指示として適切かは判定しない——判定には意味の理解が要り、機械が近似すると誤りが
本物の欠落を埋もれさせる。

記入対象がどこかは fill_template の走査に聞く。数え方をここで作り直すと、走査が
2箇所に分かれてやがて食い違う。
"""
from __future__ import annotations

from waffle.application.ports.schema_repository import SchemaRepository
from waffle.domain.services.fill_template import (
    build_prompt_coverage,
    content_def,
    discriminator_candidates,
)
from waffle.domain.services.schema_discriminator import discriminator_key
from waffle.shared.result import Err, Ok, Result

# 契約が認める指示の名前はこの2つだけ
QUERY_PROMPT = "x-prompt-query"
WRITE_PROMPT = "x-prompt-write"
DECLARED = (QUERY_PROMPT, WRITE_PROMPT)
PREFIX = "x-prompt"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _block_defs(schema: dict) -> dict:
    """引く単位。blockType の const を同一性のキーとする定義。"""
    return {name: body for name, body in schema.get("$defs", {}).items()
            if "blockType" in (body.get("properties") or {})}


def _undeclared_keys(node, path: str = "") -> list[str]:
    """契約が認めていない名前の指示を集める。綴り違い・発明されたキーがここへ落ちる。"""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith(PREFIX) and key not in DECLARED:
                found.append(f"{path}/{key}")
            else:
                found += _undeclared_keys(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found += _undeclared_keys(item, f"{path}[{i}]")
    return found


class CheckPromptContract:
    """スキーマの指示の置かれ方を確かめる。中身は見ない。"""

    def __init__(self, schemas: SchemaRepository) -> None:
        self._schemas = schemas

    def run(self, schema_ref: str) -> Result[dict]:
        """このユースケースの唯一の入口。"""
        try:
            schema = self._schemas.load(schema_ref)
        except FileNotFoundError:
            return _err("SCHEMA_NOT_FOUND", f"{schema_ref} が見つかりません")

        missing_query = [
            {"schemaRef": schema_ref, "block": name}
            for name, body in _block_defs(schema).items()
            if not body.get(QUERY_PROMPT)
        ]

        seen: set[str] = set()
        missing_write: list[dict] = []
        key = discriminator_key(schema)
        kinds = discriminator_candidates(schema, key) if key else []
        for kind in kinds or [None]:
            try:
                content = content_def(schema, {key: kind} if key and kind else {})
            except Exception:  # noqa: BLE001 — 分岐を解決できない形は走査対象外
                continue
            for leaf in build_prompt_coverage(schema, content):
                if leaf["hasPrompt"] or leaf["path"] in seen:
                    continue
                seen.add(leaf["path"])
                missing_write.append({"schemaRef": schema_ref, "path": leaf["path"]})

        undeclared = [{"schemaRef": schema_ref, "at": at}
                      for at in _undeclared_keys(schema)]

        return Ok({
            "missing_query_prompts": missing_query,
            "missing_write_prompts": missing_write,
            "undeclared_prompt_keys": undeclared,
        })

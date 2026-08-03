"""update coding preset — 実際のプロダクトで確かめた規約のうち、指定された部分だけを
プリセット（次に作るプロダクトの出発点）へ反映する application use case。

プリセットは一度書かれたきり、実践から更新される経路が無かった。プリセットから作った
プロダクトで規約の誤りを見つけて直しても、プリセットは誤ったまま残り、以後そこから
作られるすべてのプロダクトへ同じ誤りが配られ続ける。

丸ごとの写しは行わない。プロダクトの規約には、そのプロダクトが受け持つ範囲のような
固有の判断が含まれる。何が汎用かの判断は人が持ち、この操作は指定された部分の反映だけを担う。
"""
from __future__ import annotations

from waffle.application.ports.coding_preset_repository import CodingPresetRepository
from waffle.application.ports.document_repository import DocumentRepository
from waffle.shared.result import Err, Ok, Result

_CODING_PATH = ".waffle/documents/coding/{document_id}." + "json"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class UpdateCodingPreset:
    def __init__(self, documents: DocumentRepository, presets: CodingPresetRepository) -> None:
        self._documents = documents
        self._presets = presets

    def run(self, preset_name: str | None = None, from_document_id: str | None = None,
            blocks: list[str] | None = None) -> Result[dict]:
        blocks = blocks or []
        if not preset_name or not from_document_id or not blocks:
            return _err(
                "MISSING_PARAM",
                "preset、出どころの規約（from）、戻す部分（blocks）が必要です。"
                "丸ごとの写しは行わないため、戻す部分の指定は省略できません。",
            )

        try:
            preset = self._presets.load(preset_name)
        except FileNotFoundError:
            return _err("PRESET_NOT_FOUND", f"プリセットが見つかりません: {preset_name}")

        try:
            document = self._documents.load(
                _CODING_PATH.format(document_id=from_document_id))
        except FileNotFoundError:
            return _err("INVALID_PATH", f"規約が見つかりません: {from_document_id}")

        # どの種類へ反映するかは、出どころの規約が宣言している。呼び出し側に
        # 指定させると、取り違えた組み合わせを受け付けてしまう
        coding_kind = document.get("codingKind")
        if coding_kind not in preset:
            return _err(
                "UNKNOWN_BLOCK",
                f"プリセット {preset_name} は {coding_kind} を持ちません",
            )
        preset_content = preset[coding_kind]
        document_content = document.get("content", {})

        # 書き込む前に全件を確かめる。書ける分だけ書くと、プリセットが半分だけ
        # 更新された状態で残る
        missing = [b for b in blocks if b not in preset_content]
        if missing:
            return _err(
                "UNKNOWN_BLOCK",
                f"プリセット {preset_name} の {coding_kind} が持たない部分です: "
                f"{' / '.join(missing)}。プリセットの構成を変えるのは、"
                f"プリセットそのものを設計し直す別の判断です",
            )
        absent = [b for b in blocks if b not in document_content]
        if absent:
            return _err(
                "UNKNOWN_BLOCK",
                f"規約 {from_document_id} が持たない部分です: {' / '.join(absent)}",
            )

        changed = [b for b in blocks if preset_content[b] != document_content[b]]
        for block in changed:
            preset_content[block] = document_content[block]
        # 内容が一致していれば書き換えない。無変更の保存は、ファイルの更新を見ている
        # 周辺の仕組みには変更と区別がつかない（clear_field / fill と扱いを揃える）
        if changed:
            self._presets.save(preset_name, preset)

        return Ok({
            "preset": preset_name,
            "codingKind": coding_kind,
            "reflected": sorted(changed),
            "changed": bool(changed),
        })

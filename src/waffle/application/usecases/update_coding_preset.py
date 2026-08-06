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



def _split(selection: str) -> tuple[str, str | None]:
    """指定を、ブロックと、その中の欄に分ける。欄の指定が無ければ None。"""
    block, _, field = selection.partition(".")
    return block, field or None


def _absent(content: dict, selections: list[str]) -> list[str]:
    """指定のうち、その中身が持たないものを返す。欄まで指定されていれば欄まで見る。"""
    out = []
    for selection in selections:
        block, field = _split(selection)
        if block not in content:
            out.append(selection)
        elif field is not None and (not isinstance(content[block], dict)
                                    or field not in content[block]):
            out.append(selection)
    return out


def _value_at(content: dict, selection: str):
    block, field = _split(selection)
    return content[block] if field is None else content[block][field]


def _write_at(content: dict, selection: str, value) -> None:
    block, field = _split(selection)
    if field is None:
        content[block] = value
    else:
        content[block][field] = value


class UpdateCodingPreset:
    def __init__(self, documents: DocumentRepository, presets: CodingPresetRepository) -> None:
        self._documents = documents
        self._presets = presets

    def run(self, preset_name: str | None = None, from_document_id: str | None = None,
            blocks: list[str] | None = None, dry_run: bool = False) -> Result[dict]:
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
        missing = _absent(preset_content, blocks)
        if missing:
            return _err(
                "UNKNOWN_BLOCK",
                f"プリセット {preset_name} の {coding_kind} が持たない部分です: "
                f"{' / '.join(missing)}。プリセットの構成を変えるのは、"
                f"プリセットそのものを設計し直す別の判断です",
            )
        absent = _absent(document_content, blocks)
        if absent:
            return _err(
                "UNKNOWN_BLOCK",
                f"規約 {from_document_id} が持たない部分です: {' / '.join(absent)}",
            )

        changed = sorted(b for b in blocks
                         if _value_at(preset_content, b) != _value_at(document_content, b))
        # 何が汎用かの判断は人が持つ、と決めた以上、人が判断できる材料を返す。
        # ブロック名と変更の有無だけでは、その判断は誰にもできない
        reflected = [{"block": b, "before": _value_at(preset_content, b),
                      "after": _value_at(document_content, b)}
                     for b in changed]

        if changed and not dry_run:
            for selection in changed:
                _write_at(preset_content, selection, _value_at(document_content, selection))
            # 内容が一致していれば書き換えない。無変更の保存は、ファイルの更新を見ている
            # 周辺の仕組みには変更と区別がつかない（clear_field / fill と扱いを揃える）
            self._presets.save(preset_name, preset)

        return Ok({
            "preset": preset_name,
            "codingKind": coding_kind,
            "reflected": reflected,
            "changed": bool(changed),
            "applied": bool(changed) and not dry_run,
        })

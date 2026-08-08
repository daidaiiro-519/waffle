"""export skill bundle — Skillの一式を、道具立てのない相手へ持ち出せる形で
書き出す application use case（uc-export-skill-bundle）。

一式は、別の場所にある知識を指し示す形で組み立てられている。指し示しをそのまま
複製すると、渡した先では指し示す先が無く、助言を担うSkillが根拠を1つも読めない
状態で届く。しかもその壊れ方は静かで、根拠が無いとは言わずにそれらしい答えを
返してしまう。そのため書き出しは指し示しを中身そのものへ置き直し、置き直せない
ものが1つでも残れば失敗として扱う。

何を含めるかの判断は domain/services/distribution_selection が持つ。複製の手段
（指し示しの追跡）はアダプターが持つ。このusecaseは両者を順に呼ぶ調整だけを担う。
"""
from __future__ import annotations

import json
import posixpath

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services import deploy_target_resolution, distribution_selection, path_template
from waffle.shared.result import Err, Ok, Result

_SKILL_DOCUMENT_TYPE = "Skill"
_DEFAULT_DOCUMENTS_ROOT = ".waffle/documents/skills"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class ExportSkillBundle:
    """Skillの一式を、渡した先でそのまま使える形へ書き出すユースケース。"""

    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, output_path: str, documents_root: str = _DEFAULT_DOCUMENTS_ROOT) -> Result[dict]:
        """配布してよいSkillだけを選び、指し示しを中身へ置き直して書き出す。

        Args:
            output_path: 一式を書き出す先の場所。
            documents_root: Skill documentの置き場。

        Returns:
            書き出した先・含めたものの識別子・含めなかったものと理由。書き出せる
            Skillが1つも無いとき、または指し示す先の無いものが残ったときは Err。

        Raises:
            なし。失敗は Err で表す。
        """
        template = self._skill_path_template()
        if not template:
            return _err(
                "NO_SKILL_MAPPING",
                "Skillの投影先が宣言されていません（.waffle/config.json の toolMappings）",
            )

        try:
            document_paths = self._documents.list_json(documents_root)
        except (OSError, FileNotFoundError):
            document_paths = []

        exported: list[str] = []
        skipped: list[dict] = []
        sources: list[tuple[str, str]] = []
        for document_path in sorted(document_paths):
            try:
                document = self._documents.load(document_path)
            except (OSError, FileNotFoundError, ValueError):
                continue
            document_id = document.get("documentId")
            if not document_id:
                continue
            reason = distribution_selection.exclusion_reason(document)
            if reason is not None:
                skipped.append({"documentId": document_id, "reason": reason})
                continue
            source = posixpath.dirname(path_template.resolve(template, documentId=document_id))
            sources.append((document_id, source))
            exported.append(document_id)

        if not exported:
            return _err("EMPTY_BUNDLE", "書き出せるSkillが1つもありません")

        try:
            for document_id, source in sources:
                self._documents.copy_tree(
                    source,
                    posixpath.join(output_path, document_id),
                    dereference=True,
                    exclude=distribution_selection.RECEIVER_PROVIDED_SUBPATHS,
                )
        except OSError as e:
            return _err("WRITE_ERROR", f"書き出しに失敗しました: {e}")

        broken = self._documents.list_broken_links(output_path)
        if broken:
            return _err(
                "BROKEN_REFERENCE_IN_BUNDLE",
                f"指し示す先の無いものが残っています: {', '.join(sorted(broken))}",
            )

        return Ok({"path": output_path, "exported": exported, "skipped": skipped})

    def _skill_path_template(self) -> str:
        """config.json から Skill の投影先テンプレートを取り出す。

        役割の段は実体（instance）だけを見る。雛形は配置先を持たないため、
        投影されたフォルダ自体が存在せず、書き出しの対象にならない。
        """
        try:
            config = json.loads(self._documents.read_text(".waffle/config.json"))
        except (OSError, FileNotFoundError, json.JSONDecodeError):
            return ""
        for tool_config in config.get("toolMappings", {}).values():
            mapping = tool_config.get(
                deploy_target_resolution.DEFAULT_DOCUMENT_ROLE, {},
            ).get(_SKILL_DOCUMENT_TYPE)
            if isinstance(mapping, dict) and mapping.get("pathTemplate"):
                return mapping["pathTemplate"]
        return ""


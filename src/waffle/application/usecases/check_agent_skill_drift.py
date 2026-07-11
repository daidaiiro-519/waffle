"""check agent skill drift — Agent(subagent)集約の実インスタンスがskillPreloadsで
参照するSkillが実在するかを検証する application use case。

プリロード可能かどうか（Claude Code側のdisable-model-invocation等の実行時制約）は
対象外とする。実行時に自然に露見する（AIがそのSubagentとして動いた際に気づける）ため、
静的チェックとして持つ価値が薄いという判断（2026-07-11に一度実装した後、削除した）。
schema単体からは気づけない、Subagent文書↔Skill文書間の参照整合性のみを機械的に検出する。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckAgentSkillDrift:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, documents_root: str) -> Result[dict]:
        if not is_confined(documents_root):
            return _err("INVALID_PATH", f"パストラバーサルは許可されません: {documents_root}")
        try:
            self._documents.list_dirs(documents_root)
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")
        try:
            agent_paths = self._documents.list_files(f"{documents_root}/agent", "*.json")
        except FileNotFoundError:
            agent_paths = []  # Agent documentがまだ1件も無い（正常系）

        missing_skills: list[dict] = []

        for agent_path in agent_paths:
            doc = self._documents.load(agent_path)
            if doc.get("agentKind") != "subagent":
                continue
            skill_ids = doc.get("content", {}).get("skillPreloads", {}).get("items", [])
            for skill_id in skill_ids:
                skill_path = f"{documents_root}/skills/{skill_id}.json"
                try:
                    self._documents.load(skill_path)
                except FileNotFoundError:
                    missing_skills.append({"agent": agent_path, "skillId": skill_id})

        return Ok({
            "missing_skills": missing_skills,
        })

"""uc-export-skill-bundle の統合テスト（操作保証シナリオ／ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.export_skill_bundle import ExportSkillBundle
from waffle.shared.result import Err, Ok


class _RootedDocumentRepository:
    """.waffle/config.json の読み出しだけ差し替え、他は実FSへ委譲する。"""

    def __init__(self, real: FsDocumentRepository, config_json: str) -> None:
        self._real = real
        self._config_json = config_json

    def read_text(self, path: str) -> str:
        if path == ".waffle/config.json":
            return self._config_json
        return self._real.read_text(path)

    def load(self, path: str) -> dict:
        return self._real.load(path)

    def list_json(self, directory: str) -> list[str]:
        return self._real.list_json(directory)

    def copy_tree(self, source: str, destination: str, dereference: bool, exclude=()) -> None:
        self._real.copy_tree(source, destination, dereference, exclude)

    def list_broken_links(self, directory: str) -> list[str]:
        return self._real.list_broken_links(directory)


def _config(skills_root) -> str:
    return json.dumps({
        "toolMappings": {
            "some-tool": {
                "instance": {
                    "Skill": {"pathTemplate": f"{skills_root}/{{documentId}}/SKILL.md", "mode": "symlink"},
                },
            },
        },
    })


def _skill_document(tmp_path, documents_root, document_id: str, status: str) -> None:
    documents_root.mkdir(parents=True, exist_ok=True)
    (documents_root / f"{document_id}.json").write_text(json.dumps({
        "documentId": document_id, "documentType": "Skill", "schemaRef": "SkillSchema/v2",
        "status": status, "content": {},
    }), encoding="utf-8")


def _skill_tree(skills_root, document_id: str, knowledge_target=None) -> None:
    """投影されたSkillフォルダを作る。knowledge_targetを渡すとそこへのsymlinkを1本張る。"""
    skill_dir = skills_root / document_id
    (skill_dir / "references" / "knowledge").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {document_id}\n", encoding="utf-8")
    if knowledge_target is not None:
        (skill_dir / "references" / "knowledge" / "backbone.md").symlink_to(knowledge_target)


def _engine(tmp_path, skills_root) -> ExportSkillBundle:
    documents = _RootedDocumentRepository(FsDocumentRepository(), _config(str(skills_root)))
    return ExportSkillBundle(documents)


def test_repeated_export_produces_the_same_bundle(tmp_path):
    """
    Scenario: 同じ内容なら同じ一式を書き出す
    Given 元の一式が変わっていない
    When 書き出しを2回行う
    Then 2回とも同じものが同じ場所に並ぶ
    """
    skills_root = tmp_path / "projection"
    _skill_tree(skills_root, "ddd-advisor")
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "ddd-advisor", "ACTIVE")
    out = tmp_path / "bundle"
    engine = _engine(tmp_path, skills_root)

    first = engine.run(str(out), str(documents_root))
    listing_first = sorted(p.relative_to(out).as_posix() for p in out.rglob("*"))
    second = engine.run(str(out), str(documents_root))
    listing_second = sorted(p.relative_to(out).as_posix() for p in out.rglob("*"))

    assert isinstance(first, Ok) and isinstance(second, Ok)
    assert listing_first == listing_second


def test_export_does_not_change_the_source(tmp_path):
    """
    Scenario: 書き出しても元は変わらない
    Given 元の一式
    When 書き出しを行う
    Then 元の一式は書き出す前と同じままである
    """
    skills_root = tmp_path / "projection"
    knowledge = tmp_path / "store" / "backbone.md"
    knowledge.parent.mkdir(parents=True)
    knowledge.write_text("根拠の本文", encoding="utf-8")
    _skill_tree(skills_root, "ddd-advisor", knowledge_target=knowledge)
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "ddd-advisor", "ACTIVE")
    before = sorted(
        (p.relative_to(skills_root).as_posix(), p.is_symlink()) for p in skills_root.rglob("*")
    )

    result = _engine(tmp_path, skills_root).run(str(tmp_path / "bundle"), str(documents_root))

    after = sorted(
        (p.relative_to(skills_root).as_posix(), p.is_symlink()) for p in skills_root.rglob("*")
    )
    assert isinstance(result, Ok), result
    assert before == after

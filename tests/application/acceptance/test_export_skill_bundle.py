"""uc-export-skill-bundle の受け入れテスト（ネイティブpytest）。"""
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


def _skill_tree(skills_root, document_id: str, knowledge_target=None, linked_dir_target=None) -> None:
    """投影されたSkillフォルダを作る。

    実物の投影は2つの形を持つ。ファイル単位のsymlink（knowledge_target）と、
    ディレクトリごとのsymlink（linked_dir_target）である。どちらも書き出しの
    対象になるため、両方を作れるようにしておく。
    """
    skill_dir = skills_root / document_id
    (skill_dir / "references" / "knowledge").mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {document_id}\n", encoding="utf-8")
    if knowledge_target is not None:
        (skill_dir / "references" / "knowledge" / "backbone.md").symlink_to(knowledge_target)
    if linked_dir_target is not None:
        (skill_dir / "templates").symlink_to(linked_dir_target, target_is_directory=True)


def _engine(tmp_path, skills_root) -> ExportSkillBundle:
    documents = _RootedDocumentRepository(FsDocumentRepository(), _config(str(skills_root)))
    return ExportSkillBundle(documents)


def test_symlinked_knowledge_is_written_as_its_own_content(tmp_path):
    """
    Scenario: 指し示しを中身そのものへ置き直して書き出す
    Given 別の場所にある知識を指し示す形で組み立てられたSkill
    When 一式を書き出す
    Then 書き出した先には知識の中身そのものが置かれ、指し示す先の無いものは1つも残らない
    """
    skills_root = tmp_path / "projection"
    knowledge = tmp_path / "store" / "backbone.md"
    knowledge.parent.mkdir(parents=True)
    knowledge.write_text("根拠の本文", encoding="utf-8")
    templates = tmp_path / "store" / "templates"
    templates.mkdir()
    (templates / "handoff.md").write_text("雛形の本文", encoding="utf-8")
    _skill_tree(skills_root, "ddd-advisor", knowledge_target=knowledge, linked_dir_target=templates)
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "ddd-advisor", "ACTIVE")
    out = tmp_path / "bundle"

    result = _engine(tmp_path, skills_root).run(str(out), str(documents_root))

    assert isinstance(result, Ok), result
    written = out / "ddd-advisor" / "references" / "knowledge" / "backbone.md"
    assert written.is_file() and not written.is_symlink()
    assert written.read_text(encoding="utf-8") == "根拠の本文"
    linked = out / "ddd-advisor" / "templates" / "handoff.md"
    assert linked.is_file() and not linked.is_symlink()
    assert linked.read_text(encoding="utf-8") == "雛形の本文"
    assert result.value["exported"] == ["ddd-advisor"]


def test_unfinished_skill_is_left_out_with_its_reason(tmp_path):
    """
    Scenario: 仕上がっていないSkillは含めない
    Given 仕上がったSkillと、まだ仕上がっていないSkillが混在している
    When 一式を書き出す
    Then 仕上がったSkillだけが書き出され、仕上がっていないものは識別子と理由が結果に現れる
    """
    skills_root = tmp_path / "projection"
    _skill_tree(skills_root, "ddd-advisor")
    _skill_tree(skills_root, "artifact-share")
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "ddd-advisor", "ACTIVE")
    _skill_document(tmp_path, documents_root, "artifact-share", "DRAFT")
    out = tmp_path / "bundle"

    result = _engine(tmp_path, skills_root).run(str(out), str(documents_root))

    assert isinstance(result, Ok), result
    assert result.value["exported"] == ["ddd-advisor"]
    assert result.value["skipped"] == [{"documentId": "artifact-share", "reason": "NOT_READY_TO_DISTRIBUTE"}]
    assert not (out / "artifact-share").exists()


def test_unresolvable_link_makes_the_export_fail(tmp_path):
    """
    Scenario: 指し示す先の無いものが残れば失敗として扱う
    Given 中身へ置き直せない指し示しを含むSkill
    When 一式を書き出す
    Then BROKEN_REFERENCE_IN_BUNDLEが返り、その書き出しは成功として扱われない
    """
    skills_root = tmp_path / "projection"
    _skill_tree(skills_root, "ddd-advisor", knowledge_target=tmp_path / "store" / "missing.md")
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "ddd-advisor", "ACTIVE")
    out = tmp_path / "bundle"

    result = _engine(tmp_path, skills_root).run(str(out), str(documents_root))

    assert isinstance(result, Err), result
    assert result.details[0] == "BROKEN_REFERENCE_IN_BUNDLE"


def test_nothing_to_export_is_rejected(tmp_path):
    """
    Scenario: 対象が1つも無ければ書き出さない
    Given 仕上がったSkillが1つも無い
    When 一式を書き出す
    Then EMPTY_BUNDLEが返り、書き出しは行われない
    """
    skills_root = tmp_path / "projection"
    _skill_tree(skills_root, "artifact-share")
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "artifact-share", "DRAFT")
    out = tmp_path / "bundle"

    result = _engine(tmp_path, skills_root).run(str(out), str(documents_root))

    assert isinstance(result, Err), result
    assert result.details[0] == "EMPTY_BUNDLE"
    assert not out.exists()


def test_coding_standards_are_left_to_the_receiving_project(tmp_path):
    """
    Scenario: 受け取る側が自分で用意する決まりごとは含めない
    Given 受け取る側が自分で用意すべき決まりごとを抱えたSkill
    When 一式を書き出す
    Then その決まりごとは書き出されず、Skillそのものは書き出される
    """
    skills_root = tmp_path / "projection"
    _skill_tree(skills_root, "implementation")
    coding = skills_root / "implementation" / "references" / "coding"
    coding.mkdir(parents=True)
    (coding / "architecture-waffle.md").write_text("このプロジェクト固有の規約", encoding="utf-8")
    documents_root = tmp_path / "documents"
    _skill_document(tmp_path, documents_root, "implementation", "ACTIVE")
    out = tmp_path / "bundle"

    result = _engine(tmp_path, skills_root).run(str(out), str(documents_root))

    assert isinstance(result, Ok), result
    assert (out / "implementation" / "SKILL.md").is_file()
    assert not (out / "implementation" / "references" / "coding").exists()

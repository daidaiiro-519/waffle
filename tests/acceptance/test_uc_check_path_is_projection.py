"""uc-check-path-is-projection の受け入れテスト（ネイティブpytest、実configを使用）。"""
from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.shared.result import Ok


def _engine() -> CheckPathIsProjection:
    return CheckPathIsProjection(FsDocumentRepository())


def test_SkillのSKILL_mdの実体パスは投影と判定される():
    """
    Given 実体パスが".waffle/skills/ddd-advisor/SKILL.md"である
    When CheckPathIsProjectionを実行する
    Then isProjection=trueが返り、documentKind="Skill"・documentId="ddd-advisor"が返る
    """
    result = _engine().run(".waffle/skills/ddd-advisor/SKILL.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is True
    assert result.value["documentKind"] == "Skill"
    assert result.value["documentId"] == "ddd-advisor"


def test_AgentのCLAUDE_md実体パスは投影と判定される():
    """
    Given 実体パスが".waffle/agent/waffle.md"である
    When CheckPathIsProjectionを実行する
    Then isProjection=trueが返り、documentKind="Agent"・documentId="waffle"が返る
    """
    result = _engine().run(".waffle/agent/waffle.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is True
    assert result.value["documentKind"] == "Agent"
    assert result.value["documentId"] == "waffle"


def test_手書き参照ファイルの実体パスは投影と判定されない():
    """
    Given 実体パスが".waffle/skills/ddd-advisor/references/knowledge/domain-model.md"である
    When CheckPathIsProjectionを実行する
    Then isProjection=falseが返る
    """
    result = _engine().run(".waffle/skills/ddd-advisor/references/knowledge/domain-model.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is False


def test_どのcanonicalPathTemplateにも一致しないパスは投影と判定されない():
    """
    Given 実体パスが"docs/README.md"である
    When CheckPathIsProjectionを実行する
    Then isProjection=falseが返る
    """
    result = _engine().run("docs/README.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is False

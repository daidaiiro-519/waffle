"""CheckPathIsProjectionのユニットテスト（schemaのみをfakeで差し替え）。

canonicalパスの真実源はschemaのx-render-target.pathであり、config.jsonは
配置先（投影先）だけを持つ。この判定はcanonical側を見るためschemaを読む。
"""
from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.shared.result import Ok

from tests.fakes import FakeSchemaRepository

_SCHEMAS = {
    "SkillSchema/v2": {
        "properties": {"documentType": {"type": "string", "const": "Skill"}},
        "x-render-target": {"path": ".waffle/skills/{documentId}/SKILL.md"},
    },
    "AgentSchema/v3": {
        "properties": {"documentType": {"type": "string", "const": "Agent"}},
        "x-render-target": {
            "path": {
                "orchestrator": ".waffle/agent/{documentId}.md",
                "subagent": ".waffle/agent/{documentId}.md",
            },
        },
    },
}


def _engine() -> CheckPathIsProjection:
    return CheckPathIsProjection(FakeSchemaRepository(_SCHEMAS))


def test_skill_canonical_pattern_is_projection():
    """Skillのcanonicalパターンに一致すれば投影と判定する。"""
    result = _engine().run(".waffle/skills/ddd-advisor/SKILL.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": True, "documentKind": "Skill", "documentId": "ddd-advisor"}


def test_agent_canonical_pattern_is_projection():
    """discriminatorごとに宣言されたcanonicalパターンでも投影と判定する。"""
    result = _engine().run(".waffle/agent/waffle.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": True, "documentKind": "Agent", "documentId": "waffle"}


def test_unmatched_path_is_not_projection():
    """どのパターンにも一致しなければ投影ではないと判定する。"""
    result = _engine().run(".waffle/skills/ddd-advisor/references/knowledge/domain-model.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": False, "documentKind": None, "documentId": None}


def test_schema_without_render_target_is_ignored():
    """x-render-targetを持たないschemaは、判定の対象から外れるだけで例外にしない。"""
    engine = CheckPathIsProjection(FakeSchemaRepository({
        "HandoffSchema/v2": {"properties": {"documentType": {"type": "string", "const": "Handoff"}}},
    }))
    result = engine.run(".waffle/skills/ddd-advisor/SKILL.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is False

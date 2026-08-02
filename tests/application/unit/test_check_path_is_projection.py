"""CheckPathIsProjectionのユニットテスト（config.json読込のみをfakeで差し替え）。"""
import json

from waffle.application.usecases.check_path_is_projection import CheckPathIsProjection
from waffle.shared.result import Ok

_CONFIG = json.dumps({
    "canonicalPathTemplates": {
        "Skill": ".waffle/skills/{documentId}/SKILL.md",
        "Agent": ".waffle/agent/{documentId}.md",
    }
})


class _FakeDocs:
    def read_text(self, path: str) -> str:
        if path == ".waffle/config.json":
            return _CONFIG
        raise FileNotFoundError(path)


def _engine() -> CheckPathIsProjection:
    return CheckPathIsProjection(_FakeDocs())


def test_skill_canonical_pattern_is_projection():
    """Skillのcanonicalパターンに一致すれば投影と判定する。"""
    result = _engine().run(".waffle/skills/ddd-advisor/SKILL.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": True, "documentKind": "Skill", "documentId": "ddd-advisor"}


def test_agent_canonical_pattern_is_projection():
    """Agentのcanonicalパターンに一致すれば投影と判定する。"""
    result = _engine().run(".waffle/agent/waffle.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": True, "documentKind": "Agent", "documentId": "waffle"}


def test_unmatched_path_is_not_projection():
    """どのパターンにも一致しなければ投影ではないと判定する。"""
    result = _engine().run(".waffle/skills/ddd-advisor/references/knowledge/domain-model.md")
    assert isinstance(result, Ok)
    assert result.value == {"isProjection": False, "documentKind": None, "documentId": None}


def test_missing_config_falls_back_to_not_projection():
    """設定が無くても安全側で投影ではないと判定する。"""
    class _NoConfigDocs:
        def read_text(self, path: str) -> str:
            raise FileNotFoundError(path)

    result = CheckPathIsProjection(_NoConfigDocs()).run(".waffle/skills/ddd-advisor/SKILL.md")
    assert isinstance(result, Ok)
    assert result.value["isProjection"] is False

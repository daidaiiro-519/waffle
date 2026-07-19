"""uc-render-handoff-template の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.render_handoff_template import RenderHandoffTemplate
from waffle.shared.result import Err, Ok


def _write(tmp_path, name: str, doc: dict) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _handoff_doc(**overrides) -> dict:
    doc = {
        "documentId": "handoff-uc-a",
        "documentType": "Handoff",
        "schemaRef": "HandoffSchema/v1",
        "content": {
            "title": {"blockType": "Title", "title": "対象usecaseの実装引き継ぎ：handoff-uc-a"},
            "specRef": {"blockType": "SpecRef", "title": "引き継ぎ元spec", "specRef": "uc-a"},
            "designViewpoints": {
                "blockType": "DesignViewpoints", "title": "設計観点",
                "items": [
                    {"advisor": "ddd-advisor", "viewpoint": "分離が妥当", "consideration": "理由A"},
                    {"advisor": "tech-lead-advisor", "viewpoint": "配置が妥当", "consideration": "理由B"},
                ],
            },
            "implementationViewpoints": {
                "blockType": "ImplementationViewpoints", "title": "実装観点",
                "items": [
                    {"advisor": "tech-lead-advisor", "viewpoint": "既存を再利用", "consideration": "理由C"},
                ],
            },
            "constraints": {"blockType": "Constraints", "title": "既知の制約・トレードオフ", "items": ["制約1"]},
            "completionImage": {
                "blockType": "CompletionImage", "title": "完成イメージ",
                "layers": [
                    {"label": "コア", "description": "説明。", "nodes": [{"id": "a", "title": "A", "sub": "既存", "status": "existing"}]},
                ],
                "relationships": [],
            },
        },
    }
    doc["content"].update(overrides)
    return doc


def _engine() -> RenderHandoffTemplate:
    return RenderHandoffTemplate(FsDocumentRepository())


def test_completionImageを含むHandoffを描画する(tmp_path):
    """
    Given completionImage・designViewpoints・implementationViewpoints・constraints・title・specRefを持つ検証済みのHandoff
    When RenderHandoffTemplateを実行する
    Then .waffle/handoff/{documentId}.htmlが生成される
    """
    path = _write(tmp_path, "handoff-uc-a.json", _handoff_doc())
    output_path = str(tmp_path / "handoff-uc-a.html")
    result = _engine().run(path, output_path)
    assert isinstance(result, Ok), result
    assert result.value["path"] == output_path
    content = (tmp_path / "handoff-uc-a.html").read_text(encoding="utf-8")
    assert "対象usecaseの実装引き継ぎ" in content
    assert "分離が妥当" in content
    assert "既存を再利用" in content
    assert "制約1" in content


def test_HandoffSchema以外を描画しようとする(tmp_path):
    """
    Given schemaRefがHandoffSchema以外のDocument
    When RenderHandoffTemplateを実行する
    Then WRONG_SCHEMA_REFエラーが返り描画されない
    """
    doc = _handoff_doc()
    doc["schemaRef"] = "SkillSchema/v1"
    path = _write(tmp_path, "not-a-handoff.json", doc)
    result = _engine().run(path, str(tmp_path / "out.html"))
    assert isinstance(result, Err)
    assert result.details == ["WRONG_SCHEMA_REF"]


def test_completionImageが無いHandoffを描画しようとする(tmp_path):
    """
    Given completionImageブロックを持たないHandoff
    When RenderHandoffTemplateを実行する
    Then MISSING_COMPLETION_IMAGEエラーが返り描画されない
    """
    doc = _handoff_doc()
    del doc["content"]["completionImage"]
    path = _write(tmp_path, "no-image.json", doc)
    result = _engine().run(path, str(tmp_path / "out.html"))
    assert isinstance(result, Err)
    assert result.details == ["MISSING_COMPLETION_IMAGE"]


def test_advisor名と件数のペアがレビュー状況に出力される(tmp_path):
    """
    Given designViewpoints/implementationViewpointsが与えられたHandoff
    When RenderHandoffTemplateを実行する
    Then advisor名＋件数のペアがレビュー状況セクションに出力される
    """
    path = _write(tmp_path, "handoff-uc-a.json", _handoff_doc())
    output_path = str(tmp_path / "handoff-uc-a.html")
    _engine().run(path, output_path)
    content = (tmp_path / "handoff-uc-a.html").read_text(encoding="utf-8")
    assert "ddd-advisor" in content
    assert "tech-lead-advisor" in content

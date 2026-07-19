"""uc-render-document-viewer の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.render_document import RenderDocument
from waffle.application.usecases.render_document_viewer import RenderDocumentViewer
from waffle.shared.result import Err, Ok


class _FakeSchemaRepository:
    def __init__(self, schema: dict) -> None:
        self._schema = schema

    def load(self, schema_ref: str) -> dict:
        return self._schema

    def list_versions(self, name: str) -> list[str]:
        return []


def _schema():
    return {
        "properties": {
            "content": {
                "type": "object",
                "properties": {"title": {"type": "object"}, "body": {"type": "object"}},
            },
        },
        "x-render-target": {"formats": ["md"], "path": None},
        "$defs": {
            "TitleBlock": {"x-render-order": 0, "x-render-level": 1, "x-render": []},
            "BodyBlock": {
                "x-render-order": 1, "x-render-level": 2,
                "x-render": [{"as": "paragraph", "from": "text"}],
            },
        },
    }


def _engine(tmp_path):
    schema = _schema()
    schema["x-render-target"]["path"] = str(tmp_path / "canonical" / "{documentId}.md")
    real_repo = FsDocumentRepository()
    render_document = RenderDocument(real_repo, _FakeSchemaRepository(schema))
    return RenderDocumentViewer(real_repo, render_document)


def _write_doc(tmp_path, overrides=None):
    doc = {
        "documentId": "x", "schemaRef": "Fake/v1", "tags": ["domain:test"], "updatedAt": "2026-07-19T00:00:00Z",
        "content": {
            "title": {"blockType": "Title", "title": "テスト対象：x"},
            "body": {"blockType": "Body", "title": "本文", "text": "これは本文です。"},
        },
    }
    if overrides:
        doc.update(overrides)
    path = tmp_path / "doc.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_検証済みDocumentをHTMLへ描画する(tmp_path):
    """
    Given 検証済みのDocument
    When RenderDocumentViewerを実行する
    Then CSS付きの自己完結HTMLが生成され、frontmatterがヘッダに反映される
    """
    doc_path = _write_doc(tmp_path)
    output_path = str(tmp_path / "out.html")
    result = _engine(tmp_path).run(doc_path, output_path)
    assert isinstance(result, Ok), result
    html = result.value["content"]
    assert "<!doctype html>" in html
    assert "テスト対象：x" in html
    assert "domain:test" in html
    assert "<p>これは本文です。</p>" in html


def test_mermaidコードフェンスをpre要素として出力する(tmp_path):
    """
    Given 基本フローにmermaidを含むDocument
    When RenderDocumentViewerを実行する
    Then <pre class="mermaid">要素としてmermaid記法がそのまま出力される
    """
    schema = _schema()
    schema["x-render-target"]["path"] = str(tmp_path / "canonical" / "{documentId}.md")
    schema["$defs"]["BodyBlock"]["x-render"] = [{"as": "paragraph", "from": "text"}, {"as": "code", "from": "diagram", "lang": "mermaid"}]
    real_repo = FsDocumentRepository()
    render_document = RenderDocument(real_repo, _FakeSchemaRepository(schema))
    engine = RenderDocumentViewer(real_repo, render_document)

    doc_path = _write_doc(tmp_path, overrides={
        "content": {
            "title": {"blockType": "Title", "title": "テスト対象：x"},
            "body": {"blockType": "Body", "title": "本文", "text": "本文です。", "diagram": "sequenceDiagram\n  A->>B: hi"},
        },
    })
    output_path = str(tmp_path / "out.html")
    result = engine.run(doc_path, output_path)
    assert isinstance(result, Ok), result
    assert '<pre class="mermaid">' in result.value["content"]


def test_RenderDocument自体が失敗する場合はRENDER_FAILEDを返す(tmp_path):
    """
    Given RenderDocumentでMDへ描画できないDocument（schemaRef不正）
    When RenderDocumentViewerを実行する
    Then RENDER_FAILEDエラーが返りHTMLは生成されない
    """
    real_repo = FsDocumentRepository()
    render_document = RenderDocument(real_repo, _FakeSchemaRepository({}))
    engine = RenderDocumentViewer(real_repo, render_document)

    doc_path = tmp_path / "doc.json"
    doc_path.write_text(json.dumps({"documentId": "x"}), encoding="utf-8")
    output_path = str(tmp_path / "out.html")
    result = engine.run(str(doc_path), output_path)
    assert isinstance(result, Err), result
    assert result.details[0] == "RENDER_FAILED"


def test_HTML描画はDocument集約自身の状態を変更しない(tmp_path):
    """
    Given 検証済みのDocument
    When RenderDocumentViewerを実行する
    Then 対象Documentのcontent自体は変更されない（読み込んだ元ファイルのバイト列が不変）
    """
    doc_path = _write_doc(tmp_path)
    before = open(doc_path, encoding="utf-8").read()
    output_path = str(tmp_path / "out.html")
    result = _engine(tmp_path).run(doc_path, output_path)
    assert isinstance(result, Ok), result
    after = open(doc_path, encoding="utf-8").read()
    assert before == after

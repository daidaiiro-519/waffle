"""uc-render-document-graph の受け入れテスト（ネイティブpytest）。"""
import json

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.render_document_graph import RenderDocumentGraph
from waffle.shared.result import Err, Ok


def _write(tmp_path, name: str, doc: dict) -> None:
    (tmp_path / name).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _usecase_doc(doc_id: str) -> dict:
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "specKind": "usecase",
        "schemaRef": "DomainSpecSchema/v8", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": ["説明"]}},
    }


def _handoff_doc(doc_id: str, spec_ref: str) -> dict:
    return {
        "documentId": doc_id, "documentType": "Handoff", "schemaRef": "HandoffSchema/v2", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"text": "説明"}, "specRef": {"specRef": spec_ref}},
    }


def _engine() -> RenderDocumentGraph:
    return RenderDocumentGraph(FsDocumentRepository())


def test_複数documentをnode_edge付きグラフHTMLへ描画する(tmp_path):
    """
    Given bcのmembersでsubdomainを参照するDocumentと、そのsubdomainを参照するHandoff Document
    When RenderDocumentGraphを実行する
    Then 各documentがnodeとして、参照関係がedgeとして埋め込まれた自己完結HTMLファイルが生成される
    """
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    _write(tmp_path, "handoff-uc-a.json", _handoff_doc("handoff-uc-a", "uc-a"))
    output_path = str(tmp_path / "graph.html")

    result = _engine().run(str(tmp_path), output_path)
    assert isinstance(result, Ok), result
    html = result.value["content"]
    assert "<!doctype html>" in html
    assert "uc-a" in html
    assert "handoff-uc-a" in html


def test_生成済みの個別viewer_htmlがあれば全体タブがそれを参照する(tmp_path):
    """
    ユーザーフィードバック「開いた時にdescriptionのみの場合と全体のHTMLを見たい時は
    タブで切り替えできると嬉しい」を受けたが、ddd-advisor/tech-lead-advisor確認済み:
    RenderDocumentGraph自身はRenderDocumentを呼ばず、既にuc-render-document-viewerが
    生成済みの個別HTML（{documentId}.html）があればそれを参照するだけに留める。
    """
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    (tmp_path / "uc-a.html").write_text("<html>rendered</html>", encoding="utf-8")
    output_path = str(tmp_path / "graph.html")

    result = _engine().run(str(tmp_path), output_path)
    assert isinstance(result, Ok), result
    assert '<iframe src="uc-a.html"' in result.value["content"]


def test_個別viewer_html未生成なら生成コマンドを案内する(tmp_path):
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    output_path = str(tmp_path / "graph.html")

    result = _engine().run(str(tmp_path), output_path)
    assert isinstance(result, Ok), result
    assert "まだ生成されていません" in result.value["content"]
    assert "render-document-viewer" in result.value["content"]


def test_documentId形式でない参照フィールドはedge化しない(tmp_path):
    """
    Given aggregateRoot.externalRefsに概念名のみを持つaggregate Document
    When RenderDocumentGraphを実行する
    Then externalRefsはedgeとして扱われず、グラフには含まれない
    """
    doc = {
        "documentId": "agg-document", "documentType": "DomainSpec", "specKind": "aggregate",
        "schemaRef": "DomainSpecSchema/v8", "tags": [],
        "content": {
            "title": {"title": "agg-document"}, "description": {"items": ["説明"]},
            "aggregateRoot": {"name": "Document", "externalRefs": ["Schema"]},
        },
    }
    _write(tmp_path, "agg-document.json", doc)
    output_path = str(tmp_path / "graph.html")

    result = _engine().run(str(tmp_path), output_path)
    assert isinstance(result, Ok), result
    assert '"target": "Schema"' not in result.value["content"]


def test_対象ディレクトリが存在しない場合はDIRECTORY_NOT_FOUNDを返す(tmp_path):
    """
    Given 存在しないディレクトリパス
    When RenderDocumentGraphを実行する
    Then DIRECTORY_NOT_FOUNDエラーが返り描画されない
    """
    result = _engine().run(str(tmp_path / "not-exist"), str(tmp_path / "graph.html"))
    assert isinstance(result, Err), result
    assert result.details[0] == "DIRECTORY_NOT_FOUND"


def test_グラフ描画はDocument集約自身の状態を変更しない(tmp_path):
    """
    Given 検証済みのdocumentを含むディレクトリ
    When RenderDocumentGraphを実行する
    Then 対象document.jsonの内容はいずれも変更されない
    """
    doc_path = tmp_path / "uc-a.json"
    doc_path.write_text(json.dumps(_usecase_doc("uc-a"), ensure_ascii=False), encoding="utf-8")
    before = doc_path.read_text(encoding="utf-8")

    result = _engine().run(str(tmp_path), str(tmp_path / "graph.html"))
    assert isinstance(result, Ok), result
    assert doc_path.read_text(encoding="utf-8") == before

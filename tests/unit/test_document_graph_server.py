"""document_graph_server の単体テスト（実際にローカルサーバーを起動してHTTPで叩く）。"""
import json
import threading
import urllib.request

from waffle.adapters.inbound.http.document_graph_server import serve


def _write(tmp_path, name: str, doc: dict) -> None:
    (tmp_path / name).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _usecase_doc(doc_id: str) -> dict:
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "specKind": "usecase",
        "schemaRef": "DomainSpecSchema/v8", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": ["説明"]}},
    }


def test_起動すると127_0_0_1限定でリッスンする(tmp_path):
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    httpd = serve(str(tmp_path), str(tmp_path / "graph.html"), port=0)
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


def test_GETするたびに再スキャンして最新のHTMLを返す(tmp_path):
    """
    レンダリングし忘れを無くすため、ブラウザの再読み込み（GET /）だけで
    常に最新のdocument一覧が返ることを確認する（都度フルスキャン設計）。
    """
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    httpd = serve(str(tmp_path), str(tmp_path / "graph.html"), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        port = httpd.server_address[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as res:
            assert res.status == 200
            body = res.read().decode("utf-8")
        assert "<!doctype html>" in body
        assert "uc-a" in body
        assert "uc-b" not in body

        _write(tmp_path, "uc-b.json", _usecase_doc("uc-b"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as res:
            body2 = res.read().decode("utf-8")
        assert "uc-b" in body2
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_ルート以外はnot_foundを返す(tmp_path):
    _write(tmp_path, "uc-a.json", _usecase_doc("uc-a"))
    httpd = serve(str(tmp_path), str(tmp_path / "graph.html"), port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        port = httpd.server_address[1]
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/other")
            assert False, "404を期待した"
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        httpd.shutdown()
        httpd.server_close()

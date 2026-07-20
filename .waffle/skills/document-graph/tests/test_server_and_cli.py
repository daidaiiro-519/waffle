import io
import json
import urllib.request
from contextlib import redirect_stdout

import cli
import config as config_mod
import server as server_mod


def test_build_page_end_to_end(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("---\ntype: note\ntitle: A\n---\nSee [B](./b.md)\n", encoding="utf-8")
    (docs / "b.md").write_text("---\ntype: note\ntitle: B\n---\nno links\n", encoding="utf-8")

    config_mod.add_source(str(docs), alias="docs", config_path=config_path, sources_dir=sources_dir)
    html = server_mod.build_page(config_path=config_path, sources_dir=sources_dir)
    assert "A" in html and "B" in html
    assert "<svg id=\"treemapSvg\"" in html


def test_cli_add_list_remove(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("---\ntype: note\n---\nbody\n", encoding="utf-8")

    monkeypatch.setattr(config_mod, "DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setattr(config_mod, "DEFAULT_SOURCES_DIR", sources_dir)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["add", str(docs), "--alias", "docs"])
    assert rc == 0
    assert "追加しました" in buf.getvalue()

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["list"])
    assert rc == 0
    assert "docs" in buf.getvalue()

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(["remove", "docs"])
    assert rc == 0
    assert config_mod.list_sources(config_path) == []


def test_server_serves_graph_and_source_file(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("---\ntype: note\ntitle: A\n---\nbody\n", encoding="utf-8")
    config_mod.add_source(str(docs), alias="docs", config_path=config_path, sources_dir=sources_dir)

    httpd = server_mod.make_server(port=0, config_path=config_path, sources_dir=sources_dir)
    port = httpd.server_address[1]
    import threading

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "A" in body

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/files/docs/a.md") as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "body" in body
    finally:
        httpd.shutdown()
        thread.join(timeout=5)

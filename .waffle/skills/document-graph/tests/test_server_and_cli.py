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


def test_全体タブはmd形式ソースをcss整形済みhtmlへ変換して返す(tmp_path):
    """
    Given MD形式で登録されたsource
    When /preview/{alias}/{relpath} をGETする
    Then markdown_to_html.convert相当のHTML本文と、ビューア用CSS（documentViewer相当）が
    含まれる自己完結HTMLが返る（旧Waffle uc-render-document-viewerと同等の見た目）
    """
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text(
        "---\ntype: note\ntitle: A\ndescription: 説明文\nschemaRef: DomainSpecSchema/v8\n"
        "updatedAt: '2026-07-20T00:00:00Z'\n---\n# 見出し\n\n本文です。\n",
        encoding="utf-8",
    )
    (docs / "b.md").write_text("---\ntype: note\ntitle: B\n---\nschemaRef/updatedAtが無いdocument\n", encoding="utf-8")
    config_mod.add_source(str(docs), alias="docs", config_path=config_path, sources_dir=sources_dir)

    httpd = server_mod.make_server(port=0, config_path=config_path, sources_dir=sources_dir)
    port = httpd.server_address[1]
    import threading

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/preview/docs/a.md") as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "<h1>見出し</h1>" in body
            assert "<p>本文です。</p>" in body
            assert "説明文" in body
            assert "article {" in body  # ビューアCSSが埋め込まれている
            # Waffle本体のuc-render-document-viewerと同一のmasthead構成（documentId/schemaRef/updatedAt）
            assert "<dt>documentId</dt><dd>a</dd>" in body
            assert "<dt>schemaRef</dt><dd>DomainSpecSchema/v8</dd>" in body
            assert "<dt>updatedAt</dt><dd>2026-07-20T00:00:00Z</dd>" in body

        # schemaRef/updatedAtを持たない（Waffle以外の起源を想定した）documentでは行ごと省略される
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/preview/docs/b.md") as resp:
            body = resp.read().decode("utf-8")
            assert "<dt>documentId</dt><dd>b</dd>" in body
            assert "<dt>schemaRef</dt>" not in body
            assert "<dt>updatedAt</dt>" not in body
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


def test_全体タブのリンクはhtml形式は直接_md形式はpreview経由になる(tmp_path):
    """
    Given HTML形式とMD形式、両方のsourceを持つ構成
    When グラフページを生成する
    Then HTML形式の「全体」タブは/filesへ、MD形式の「全体」タブは/previewへiframeする
    """
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    md_docs = tmp_path / "md_docs"
    md_docs.mkdir()
    (md_docs / "a.md").write_text("---\ntype: note\ntitle: A\n---\nbody\n", encoding="utf-8")
    html_docs = tmp_path / "html_docs"
    html_docs.mkdir()
    (html_docs / "b.html").write_text(
        '<html><head><meta name="type" content="page"><meta name="title" content="B"></head><body>b</body></html>',
        encoding="utf-8",
    )
    config_mod.add_source(str(md_docs), alias="md-docs", fmt="md", config_path=config_path, sources_dir=sources_dir)
    config_mod.add_source(str(html_docs), alias="html-docs", fmt="html", config_path=config_path, sources_dir=sources_dir)

    html = server_mod.build_page(config_path=config_path, sources_dir=sources_dir)
    assert '<iframe src="/preview/md-docs/a.md"' in html
    assert '<iframe src="/files/html-docs/b.html"' in html

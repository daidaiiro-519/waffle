from graph_viewer_html_template import render_graph_html


def _sample_graph():
    return {
        "nodes": [
            {"id": "a", "type": "note", "title": "A文書", "description": "説明A", "tags": [], "href": "docs/a.md"},
            {"id": "b", "type": "note", "title": "B文書", "description": "説明B", "tags": [], "href": "docs/b.md"},
        ],
        "edges": [{"from": "a", "to": "b"}],
    }


def test_render_graph_html_includes_treemap_and_panels():
    html = render_graph_html(_sample_graph())
    assert "<svg id=\"treemapSvg\"" in html
    assert "A文書" in html
    assert "B文書" in html


def test_render_graph_html_links_to_original_file_via_files_prefix():
    html = render_graph_html(_sample_graph(), files_base_url="/files/")
    assert 'href="/files/docs/a.md"' in html
    assert 'href="/files/docs/b.md"' in html


def test_render_graph_html_no_speckind_or_schemaref_reference():
    html = render_graph_html(_sample_graph())
    assert "specKind" not in html
    assert "schemaRef" not in html


def test_render_graph_html_shows_warnings():
    html = render_graph_html(_sample_graph(), warnings=["ファイル名の重複: 'x'"])
    assert "ファイル名の重複" in html


def test_render_graph_html_empty_graph_has_no_treemap_section():
    html = render_graph_html({"nodes": [], "edges": []})
    assert "<section class=\"treemap\">" not in html

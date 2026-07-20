from pathlib import Path

import graph_index


def test_parse_md_frontmatter_flat_and_inline_list():
    text = (
        "---\n"
        "type: note\n"
        'title: "サンプル"\n'
        "description: 説明文\n"
        'tags: ["a", "b"]\n'
        "---\n"
        "本文\n"
    )
    fm, body = graph_index.parse_md(text)
    assert fm == {"type": "note", "title": "サンプル", "description": "説明文", "tags": ["a", "b"]}
    assert body.strip() == "本文"


def test_parse_md_frontmatter_list_dash_form():
    text = "---\ntags:\n  - a\n  - b\n---\nbody\n"
    fm, _ = graph_index.parse_md(text)
    assert fm["tags"] == ["a", "b"]


def test_parse_md_no_frontmatter():
    fm, body = graph_index.parse_md("# heading\nbody text")
    assert fm == {}
    assert body == "# heading\nbody text"


def test_parse_html_meta_reads_contract_fields():
    text = (
        "<html><head>"
        '<meta name="type" content="doc">'
        '<meta name="title" content="タイトル">'
        '<meta name="description" content="desc">'
        '<meta name="tags" content="a, b">'
        "</head><body></body></html>"
    )
    meta = graph_index.parse_html_meta(text)
    assert meta == {"type": "doc", "title": "タイトル", "description": "desc", "tags": ["a", "b"]}


def test_parse_html_meta_title_fallback_to_title_tag():
    text = "<html><head><title>フォールバック</title></head><body></body></html>"
    meta = graph_index.parse_html_meta(text)
    assert meta["title"] == "フォールバック"


def test_scan_sources_builds_nodes_and_edges(tmp_path):
    root = tmp_path
    alias_dir = root / "docs"
    alias_dir.mkdir()
    (alias_dir / "a.md").write_text(
        '---\ntype: note\ntitle: A\n---\nSee [B](./b.md) for detail.\n', encoding="utf-8"
    )
    (alias_dir / "b.md").write_text('---\ntype: note\ntitle: B\n---\nback to nothing.\n', encoding="utf-8")

    sources = [{"alias": "docs", "path": str(alias_dir), "format": "md"}]
    graph = graph_index.scan_sources(root, sources)

    ids = {n["id"] for n in graph["nodes"]}
    assert ids == {"a", "b"}
    assert {"from": "a", "to": "b"} in graph["edges"]
    assert graph["duplicates"] == {}


def test_scan_sources_html_link_resolution(tmp_path):
    root = tmp_path
    alias_dir = root / "docs"
    alias_dir.mkdir()
    (alias_dir / "x.html").write_text(
        '<html><head><meta name="type" content="page"></head>'
        '<body><a href="y.html">link</a></body></html>',
        encoding="utf-8",
    )
    (alias_dir / "y.html").write_text(
        '<html><head><meta name="type" content="page"></head><body>no links</body></html>',
        encoding="utf-8",
    )
    sources = [{"alias": "docs", "path": str(alias_dir), "format": "html"}]
    graph = graph_index.scan_sources(root, sources)
    assert {"from": "x", "to": "y"} in graph["edges"]


def test_scan_sources_ignores_external_links(tmp_path):
    root = tmp_path
    alias_dir = root / "docs"
    alias_dir.mkdir()
    (alias_dir / "a.md").write_text(
        "---\ntype: note\n---\n[external](https://example.com/page) and [nowhere](./missing.md)\n",
        encoding="utf-8",
    )
    sources = [{"alias": "docs", "path": str(alias_dir), "format": "md"}]
    graph = graph_index.scan_sources(root, sources)
    assert graph["edges"] == []


def test_scan_sources_detects_duplicate_filenames_across_sources(tmp_path):
    root = tmp_path
    a_dir = root / "a"
    b_dir = root / "b"
    a_dir.mkdir()
    b_dir.mkdir()
    (a_dir / "dup.md").write_text("---\ntype: note\n---\nA version\n", encoding="utf-8")
    (b_dir / "dup.md").write_text("---\ntype: note\n---\nB version\n", encoding="utf-8")

    sources = [
        {"alias": "a", "path": str(a_dir), "format": "md"},
        {"alias": "b", "path": str(b_dir), "format": "md"},
    ]
    graph = graph_index.scan_sources(root, sources)
    assert "dup" in graph["duplicates"]
    assert len(graph["duplicates"]["dup"]) == 2
    assert graph["warnings"]
    # 重複IDは最初の1件のみグラフに採用される（KeyErrorを避けるための単純化）
    assert sum(1 for n in graph["nodes"] if n["id"] == "dup") == 1


def test_scan_sources_contract_missing_counts(tmp_path):
    root = tmp_path
    alias_dir = root / "docs"
    alias_dir.mkdir()
    (alias_dir / "with_fm.md").write_text("---\ntype: note\n---\nbody\n", encoding="utf-8")
    (alias_dir / "no_fm.md").write_text("just plain text\n", encoding="utf-8")

    sources = [{"alias": "docs", "path": str(alias_dir), "format": "md"}]
    graph = graph_index.scan_sources(root, sources)
    assert graph["contractMissing"]["docs"] == 1
    assert graph["contractTotal"]["docs"] == 2


def test_node_href_relative_to_alias_dir(tmp_path):
    root = tmp_path
    alias_dir = root / "docs"
    nested = alias_dir / "sub"
    nested.mkdir(parents=True)
    (nested / "c.md").write_text("---\ntype: note\n---\nbody\n", encoding="utf-8")

    sources = [{"alias": "docs", "path": str(alias_dir), "format": "md"}]
    graph = graph_index.scan_sources(root, sources)
    node = next(n for n in graph["nodes"] if n["id"] == "c")
    assert node["href"] == "docs/sub/c.md"


def test_compute_categories_groups_by_type_and_related():
    graph = {
        "nodes": [
            {"id": "a", "type": "note", "title": "A", "description": "", "tags": [], "href": "x/a.md"},
            {"id": "b", "type": "note", "title": "B", "description": "", "tags": [], "href": "x/b.md"},
            {"id": "c", "type": "page", "title": "C", "description": "", "tags": [], "href": "x/c.html"},
        ],
        "edges": [{"from": "a", "to": "b"}, {"from": "a", "to": "c"}],
    }
    categories = graph_index.compute_categories(graph)
    by_label = {c["label"]: c for c in categories}
    assert set(by_label) == {"note", "page"}
    a_doc = next(d for d in by_label["note"]["docs"] if d["id"] == "a")
    related_ids = {r["id"] for r in a_doc["related"]}
    assert related_ids == {"b", "c"}


def test_compute_categories_unclassified_label_for_empty_type():
    graph = {
        "nodes": [{"id": "a", "type": "", "title": "A", "description": "", "tags": [], "href": "x/a.md"}],
        "edges": [],
    }
    categories = graph_index.compute_categories(graph)
    assert categories[0]["label"] == "(未分類)"

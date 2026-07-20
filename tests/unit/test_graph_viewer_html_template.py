"""graph_viewer_html_template の単体テスト。"""
from waffle.domain.services.graph_index import build_graph
from waffle.domain.services.graph_viewer_html_template import render_graph_html


def _bc(members):
    return {
        "documentId": "bc-waffle", "documentType": "DomainSpec", "schemaRef": "DomainSpecSchema/v8",
        "specKind": "bounded-context", "tags": [],
        "content": {
            "title": {"title": "bc"}, "description": {"items": ["bcの概要"]},
            "members": {"items": members},
        },
    }


def _subdomain(doc_id, members):
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "schemaRef": "DomainSpecSchema/v8",
        "specKind": "subdomain", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": ["説明"]}, "members": {"items": members}},
    }


def _usecase(doc_id, description="説明A"):
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "schemaRef": "DomainSpecSchema/v8",
        "specKind": "usecase", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": [description]}},
    }


def _spec(doc_id, spec_kind):
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "schemaRef": "DomainSpecSchema/v8",
        "specKind": spec_kind, "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": ["説明"]}},
    }


def _handoff(doc_id, spec_ref):
    return {
        "documentId": doc_id, "documentType": "Handoff", "schemaRef": "HandoffSchema/v2", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"text": "説明"}, "specRef": {"specRef": spec_ref}},
    }


def test_treemapがspecKind別のフラットなカテゴリ箱として描画される():
    docs = [
        _bc([{"kind": "subdomain", "members": ["sd-a"]}, {"kind": "aggregate", "members": ["agg-a"]}]),
        _subdomain("sd-a", ["uc-a"]), _spec("agg-a", "aggregate"), _usecase("uc-a"),
    ]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert 'data-cat-key="cat::bounded-context"' in html
    assert 'data-cat-key="cat::subdomain"' in html
    assert 'data-cat-key="cat::aggregate"' in html
    assert 'data-cat-key="cat::usecase"' in html


def test_各カテゴリのパネルに個別documentとその説明が出る():
    docs = [_usecase("uc-a", description="説明A")]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert "uc-a" in html
    assert "説明A" in html
    assert 'id="panel-cat::usecase"' in html


def test_紐づき先はカテゴリ別に折りたたまれたツリーとして表示される():
    """
    ユーザーフィードバック「リンクの表現をツリーにしないと。こんなリンクを
    いっぱい貼られても困りますわ」を受け、平坦な🔗バッジ列ではなく、カテゴリ別に
    件数だけ見えて中身は開くまで畳まれているツリー表示に変更した。
    """
    docs = [_bc([{"kind": "usecase", "members": ["uc-a"]}]), _usecase("uc-a"), _handoff("handoff-uc-a", "uc-a")]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert "related-badge" not in html
    assert 'class="rel-group"' in html
    assert "Handoff (1件)" in html
    assert "handoff-uc-a" in html


def test_紐づき先はクリックで対象カテゴリと対象documentへ飛べるリンクになる():
    """
    ユーザーフィードバック「紐づき先に飛べるようにできないかな？treemapでその
    documentを選択した時と同じ遷移にできない？」を受け、related項目をtreemapの
    カテゴリ選択と同じ状態遷移（selectCategory）＋該当document行へのスクロール
    フォーカスを行うリンクにした。
    """
    docs = [_bc([{"kind": "usecase", "members": ["uc-a"]}]), _usecase("uc-a"), _handoff("handoff-uc-a", "uc-a")]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert 'id="doc-handoff-uc-a"' in html
    assert 'class="rel-link" data-cat-key="cat::Handoff" data-doc-id="handoff-uc-a"' in html
    assert "selectCategory" in html


def test_概要タブと全体タブが切り替えできる():
    """
    ユーザーフィードバック「開いた時にdescriptionのみの場合と全体のHTMLを見たい時は
    タブで切り替えできると嬉しい」を受け、各document行に概要/全体のタブを追加した。
    ただしuc-render-document-graphは軽量な集計投影usecaseでありRenderDocumentは
    呼ばない設計（ddd-advisor/tech-lead-advisor確認済み）のため、全体タブは
    uc-render-document-viewerが既に生成した個別HTMLへの参照に留める。
    """
    docs = [_usecase("uc-a")]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert 'data-tab="desc"' in html
    assert 'data-tab="full"' in html
    assert 'class="tab-pane tab-desc active"' in html
    assert 'class="tab-pane tab-full"' in html


def test_全体タブは生成済みviewer_htmlがあればiframeで参照する():
    docs = [_usecase("uc-a")]
    graph = build_graph(docs)
    html = render_graph_html(graph, viewer_available={"uc-a": "uc-a.html"})
    assert '<iframe src="uc-a.html"' in html


def test_全体タブはviewer_html未生成なら生成コマンドを案内する():
    docs = [_usecase("uc-a")]
    graph = build_graph(docs)
    html = render_graph_html(
        graph, path_by_id={"uc-a": ".waffle/documents/specs/bc-waffle/subdomain/sd-a/usecase/uc-a.json"}
    )
    assert "まだ生成されていません" in html
    assert "render-document-viewer" in html
    assert ".waffle/documents/specs/bc-waffle/subdomain/sd-a/usecase/uc-a.json" in html


def test_紐づき先がないdocumentには紐づき先なしと表示される():
    docs = [_usecase("orphan-uc")]
    graph = build_graph(docs)
    html = render_graph_html(graph)
    assert "紐づき先なし" in html


def test_検索入力が1つだけあり複雑なツールバーは持たない():
    html = render_graph_html({"nodes": [], "edges": []})
    assert 'id="search"' in html
    assert "typeFilter" not in html
    assert "layout" not in html.lower()


def test_cytoscapeなど力指向グラフライブラリに依存しない():
    """
    ユーザーフィードバック（力指向グラフの多機能UIが使いにくい、種別ごとの平坦なリストも
    包含階層treeも価値がない、specKind自体をカテゴリタグとして最上位に置いてほしい）を
    受け、specKind/documentType別のフラットなカテゴリ→document一覧（紐づき先つき）という
    ドリルダウン型のtreemapへ設計を収束させた。
    """
    html = render_graph_html({"nodes": [], "edges": []})
    assert "cytoscape" not in html.lower()


def test_自己完結htmlになる():
    html = render_graph_html({"nodes": [], "edges": []})
    assert "<!doctype html>" in html
    assert "<html>" in html

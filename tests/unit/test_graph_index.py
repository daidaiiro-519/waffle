"""graph_index の単体テスト（documentId形式で正しく取得できる4種の参照フィールドからnode/edgeを集計する）。"""
from waffle.domain.services.graph_index import build_graph, compute_categories


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


def _usecase(doc_id):
    return {
        "documentId": doc_id, "documentType": "DomainSpec", "schemaRef": "DomainSpecSchema/v8",
        "specKind": "usecase", "tags": [],
        "content": {"title": {"title": doc_id}, "description": {"items": ["説明"]}},
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


def _knowledge(doc_id, related_ids):
    return {
        "documentId": doc_id, "documentType": "Knowledge", "schemaRef": "KnowledgeSchema/v4", "tags": [],
        "content": {
            "title": {"title": doc_id}, "description": {"text": "説明"},
            "relatedConcepts": {"items": [{"conceptId": rid} for rid in related_ids]},
        },
    }


def test_bcのmembersからkind別にedgeを抽出する():
    docs = [
        _bc([{"kind": "subdomain", "members": ["sd-a"]}, {"kind": "usecase", "members": ["uc-a"]}]),
        _subdomain("sd-a", []), _usecase("uc-a"),
    ]
    graph = build_graph(docs)
    pairs = {(e["from"], e["to"]) for e in graph["edges"]}
    assert ("bc-waffle", "sd-a") in pairs
    assert ("bc-waffle", "uc-a") in pairs


def test_subdomainのmembersからedgeを抽出する():
    docs = [_subdomain("sd-a", ["uc-a", "uc-b"]), _usecase("uc-a"), _usecase("uc-b")]
    graph = build_graph(docs)
    pairs = {(e["from"], e["to"]) for e in graph["edges"]}
    assert ("sd-a", "uc-a") in pairs
    assert ("sd-a", "uc-b") in pairs


def test_handoffのspecRefからedgeを抽出する():
    docs = [_handoff("handoff-uc-a", "uc-a"), _usecase("uc-a")]
    graph = build_graph(docs)
    pairs = {(e["from"], e["to"]) for e in graph["edges"]}
    assert ("handoff-uc-a", "uc-a") in pairs


def test_knowledgeのrelatedConceptsからedgeを抽出する():
    docs = [
        _knowledge("bounded-context", ["subdomain", "ubiquitous-language"]),
        _knowledge("subdomain", []), _knowledge("ubiquitous-language", []),
    ]
    graph = build_graph(docs)
    pairs = {(e["from"], e["to"]) for e in graph["edges"]}
    assert ("bounded-context", "subdomain") in pairs
    assert ("bounded-context", "ubiquitous-language") in pairs


def test_全documentがnodeとして含まれる():
    docs = [_usecase("uc-a"), _handoff("handoff-uc-a", "uc-a")]
    graph = build_graph(docs)
    ids = {n["id"] for n in graph["nodes"]}
    assert ids == {"uc-a", "handoff-uc-a"}


def test_nodeはtitle_description_tagsを持つ():
    docs = [_usecase("uc-a")]
    graph = build_graph(docs)
    node = graph["nodes"][0]
    assert node["id"] == "uc-a"
    assert node["type"] == "DomainSpec"
    assert node["title"] == "uc-a"
    assert node["description"] == "説明"


def test_未知の参照先を指すedgeは生成しない():
    """存在しないdocumentIdを参照するmembersは、node集合に無いのでedgeから除外する。"""
    docs = [_bc([{"kind": "usecase", "members": ["uc-not-exist"]}])]
    graph = build_graph(docs)
    assert graph["edges"] == []


def test_compute_categoriesはDomainSpecをspecKind別のカテゴリへ分類する():
    """
    ユーザー指摘: 「文脈境界・集約・サブドメインのタグがない、名称が展開されている」を受け、
    個別documentの固有名ではなくspecKind自体を最上位カテゴリのラベルにする。
    """
    docs = [
        _bc([{"kind": "subdomain", "members": ["sd-a"]}, {"kind": "aggregate", "members": ["agg-a"]}]),
        _subdomain("sd-a", ["uc-a"]), _spec("agg-a", "aggregate"), _spec("uc-a", "usecase"),
    ]
    graph = build_graph(docs)
    categories = compute_categories(graph)
    labels = {c["label"]: c["count"] for c in categories}
    assert labels == {"bounded-context": 1, "subdomain": 1, "aggregate": 1, "usecase": 1}


def test_compute_categoriesはDomainSpec以外をdocumentType別のカテゴリへ分類する():
    docs = [_usecase("uc-a"), _handoff("handoff-uc-a", "uc-a"), _knowledge("kn-a", [])]
    graph = build_graph(docs)
    categories = compute_categories(graph)
    labels = {c["label"] for c in categories}
    assert "Handoff" in labels
    assert "Knowledge" in labels


def test_compute_categoriesは各documentにedgeで繋がる相手をカテゴリラベル付きでrelatedとして持つ():
    """
    relatedにカテゴリラベル（specKind/documentType）を持たせるのは、件数が多い
    documentでrelatedを平坦なバッジ羅列にすると読めなくなるため（ユーザー
    フィードバック「リンクの表現をツリーにしないと」）。呼び出し側でカテゴリ別に
    折りたたむツリーとして描画できるようにする。
    """
    docs = [_usecase("uc-a"), _handoff("handoff-uc-a", "uc-a")]
    graph = build_graph(docs)
    categories = compute_categories(graph)
    usecase_doc = next(d for c in categories for d in c["docs"] if d["id"] == "uc-a")
    handoff_doc = next(d for c in categories for d in c["docs"] if d["id"] == "handoff-uc-a")
    assert usecase_doc["related"] == [{"id": "handoff-uc-a", "title": "handoff-uc-a", "category": "Handoff"}]
    assert handoff_doc["related"] == [{"id": "uc-a", "title": "uc-a", "category": "usecase"}]


def test_compute_categoriesは件数降順で並ぶ():
    docs = [_usecase("uc-a"), _usecase("uc-b"), _usecase("uc-c"), _handoff("handoff-uc-a", "uc-a")]
    graph = build_graph(docs)
    categories = compute_categories(graph)
    assert categories[0]["label"] == "usecase"
    assert categories[0]["count"] == 3

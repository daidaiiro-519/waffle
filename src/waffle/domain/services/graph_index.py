"""graph_index — 複数documentを横断し、documentId形式で正しく取得できる参照
フィールドからnode/edgeを集計し、specKind（DomainSpec）/documentType（それ以外）別の
フラットなカテゴリへ分類する純粋関数群。uc-render-document-graphが使う。

edge抽出はdocumentId形式で正しく取得できる4種のみを対象にする（investigation
Skillの事前調査で判明、ddd-advisor確認済み）:
- DomainSpec（bounded-context）: content.members.items[].members（kind別配列）
- DomainSpec（subdomain）: content.members.items（配列）
- Handoff: content.specRef.specRef（単一参照）
- Knowledge: content.relatedConcepts.items[].conceptId（配列）

aggregateRoot.externalRefs（概念名のみ）・knowledgeRefs.path（ファイルパス）・
usecaseRef.text（uc-プレフィックス欠落）はdocumentId形式でないため対象外
（バグではなくスコープ限定）。

設計の変遷（ユーザーフィードバックを都度反映）: 力指向グラフ→種別グルーピングの
平坦リスト→bc/subdomain包含階層のtree→treemap（subdomain→specKindの2階層ネスト）
→本設計（specKind/documentTypeによるフラットなカテゴリ＋カテゴリ選択→個別document
選択→紐づく相手を表示、というドリルダウン型UX）。「文脈境界・集約・サブドメインの
タグがない、名称が展開されてしまっている」という指摘を受け、個別documentの固有名
（例: 特定のsubdomainの業務名）を最上位の分類軸に使うのをやめ、specKind自体
（bounded-context/subdomain/aggregate/usecase等）をカテゴリタグとして最上位に
置く設計へ変更した。
"""
from __future__ import annotations


def _node_description(content: dict) -> str:
    block = content.get("description", {})
    return block.get("text") or " ".join(block.get("items", []))


def _extract_refs(doc: dict) -> list[str]:
    content = doc.get("content", {})
    document_type = doc.get("documentType")
    spec_kind = doc.get("specKind")

    if document_type == "DomainSpec" and spec_kind == "bounded-context":
        refs = []
        for group in content.get("members", {}).get("items", []):
            refs.extend(group.get("members", []))
        return refs

    if document_type == "DomainSpec" and spec_kind == "subdomain":
        return list(content.get("members", {}).get("items", []))

    if document_type == "Handoff":
        spec_ref = content.get("specRef", {}).get("specRef")
        return [spec_ref] if spec_ref else []

    if document_type == "Knowledge":
        return [item["conceptId"] for item in content.get("relatedConcepts", {}).get("items", [])]

    return []


def build_graph(docs: list[dict]) -> dict:
    """documentのリストから{"nodes": [...], "edges": [...]}を組み立てる。"""
    nodes = []
    known_ids = set()
    for doc in docs:
        doc_id = doc["documentId"]
        known_ids.add(doc_id)
        content = doc.get("content", {})
        nodes.append({
            "id": doc_id,
            "type": doc.get("documentType", ""),
            "specKind": doc.get("specKind"),
            "schemaRef": doc.get("schemaRef", ""),
            "title": content.get("title", {}).get("title", doc_id),
            "description": _node_description(content),
            "tags": doc.get("tags", []),
        })

    edges = []
    for doc in docs:
        doc_id = doc["documentId"]
        for ref in _extract_refs(doc):
            if ref in known_ids:
                edges.append({"from": doc_id, "to": ref})

    return {"nodes": nodes, "edges": edges}


def compute_categories(graph: dict) -> list[dict]:
    """全nodeを、DomainSpecはspecKind別（bounded-context/subdomain/aggregate/usecase等）、
    それ以外はdocumentType別（Handoff/Knowledge等）のフラットなカテゴリへ分類する。
    各documentには、どちらの向きのedgeでも繋がる相手を"related"として（相手の
    カテゴリラベル付きで）あらかじめ埋め込む（カテゴリ選択→個別document選択→
    紐づく相手を見る、というドリルダウンUXのため。ユーザーフィードバック:
    「カテゴリを選んで、選んだものが何と紐づくかわかるのが一番UXが良い」）。
    relatedにカテゴリラベルを持たせるのは、件数が多いdocument（例: 多数のusecase
    を抱えるsubdomain）でrelatedを平坦なバッジの羅列にすると読めなくなるため
    （ユーザーフィードバック「リンクの表現をツリーにしないと」）。呼び出し側
    （graph_viewer_html_template）でカテゴリ別に折りたたむツリーとして描画する。
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    def _label(n: dict) -> str:
        return n["specKind"] if n["type"] == "DomainSpec" and n["specKind"] else n["type"]

    related: dict[str, set[str]] = {}
    for e in graph["edges"]:
        related.setdefault(e["from"], set()).add(e["to"])
        related.setdefault(e["to"], set()).add(e["from"])

    groups: dict[str, dict] = {}
    for n in graph["nodes"]:
        label = _label(n)
        key = f"cat::{label}"
        groups.setdefault(key, {"key": key, "label": label, "count": 0, "docs": []})
        groups[key]["count"] += 1
        related_items = sorted(
            (
                {"id": rid, "title": nodes_by_id[rid]["title"], "category": _label(nodes_by_id[rid])}
                for rid in related.get(n["id"], set()) if rid in nodes_by_id
            ),
            key=lambda r: (r["category"], r["title"]),
        )
        groups[key]["docs"].append({
            "id": n["id"], "title": n["title"], "description": n["description"], "related": related_items,
        })

    for g in groups.values():
        g["docs"].sort(key=lambda d: d["title"])
    return sorted(groups.values(), key=lambda g: -g["count"])

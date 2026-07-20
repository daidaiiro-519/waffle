"""render document graph — 複数documentを横断してnode/edgeを集計し、
力指向グラフの自己完結HTMLへ描画するapplication use case
（uc-render-document-graph）。

QueryDocumentCollection同型のパターン（ディレクトリ横断・都度フルスキャン・
永続インデックスなし）を踏襲する（tech-lead-advisor助言）。RenderDocumentは
呼ばない——グラフはMD描画結果ではなくdocument.jsonのメタデータ・参照フィールド
の集計であるため。読み取り専用の投影であり、Document集約自身の状態は変更しない。

各documentの「全体」タブは、uc-render-document-viewerが既に生成済みの個別HTML
（出力先ディレクトリ直下の{documentId}.html）が存在すればそれを参照するだけで、
本usecase自身はRenderDocument/markdown_to_htmlを呼ばずMD本文を描画しない
（ユーザーフィードバック「開いた時に全体のHTMLをタブで見たい」を受けて検討したが、
ddd-advisor/tech-lead-advisor確認済み: 埋め込み描画は責務逸脱・出力肥大化のため、
既存の個別viewer生成物への参照のみに留める）。
"""
from __future__ import annotations

import posixpath

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.graph_index import build_graph
from waffle.domain.services.graph_viewer_html_template import render_graph_html
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class RenderDocumentGraph:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, directory: str, output_path: str) -> Result[dict]:
        try:
            paths = self._documents.list_files(directory, "**/*.json")
        except FileNotFoundError:
            return _err("DIRECTORY_NOT_FOUND", f"ディレクトリが見つかりません: {directory}")

        docs = []
        path_by_id: dict[str, str] = {}
        for path in paths:
            try:
                doc = self._documents.load(path)
            except (OSError, ValueError):
                continue
            docs.append(doc)
            path_by_id[doc["documentId"]] = path

        graph = build_graph(docs)

        view_dir = posixpath.dirname(output_path) or "."
        try:
            existing_html = self._documents.list_files(view_dir, "*.html")
        except FileNotFoundError:
            existing_html = []
        viewer_available = {
            stem: posixpath.basename(p)
            for p in existing_html
            if (stem := posixpath.basename(p).removesuffix(".html")) in path_by_id
        }

        html = render_graph_html(graph, viewer_available=viewer_available, path_by_id=path_by_id)

        try:
            self._documents.write_text(output_path, html)
        except OSError as e:
            return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")

        return Ok({"path": output_path, "content": html})

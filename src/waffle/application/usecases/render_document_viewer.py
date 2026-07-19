"""render document viewer — MD正本をCSS付きの自己完結HTMLへ変換する
application use case（uc-render-document-viewer）。

MD正本（RenderDocument、コマンド実行モデル）とHTML投影（読み取り専用）をCQRS原則で
分離する（ddd-advisor助言）。内部でRenderDocumentをdeploy=falseで呼び、MD文字列と
frontmatter用の属性だけを取得する。Document集約自身の状態・内容は変更しない。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.services.document_loading import load_document
from waffle.application.usecases.render_document import RenderDocument
from waffle.domain.services.document_viewer_html_template import render_viewer_html
from waffle.domain.services.markdown_to_html import convert
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class RenderDocumentViewer:
    def __init__(self, documents: DocumentRepository, render_document: RenderDocument) -> None:
        self._documents = documents
        self._render_document = render_document

    def run(self, document_path: str, output_path: str) -> Result[dict]:
        rendered = self._render_document.run(document_path, deploy=False)
        if isinstance(rendered, Err):
            return _err("RENDER_FAILED", f"MDへの描画に失敗しました: {rendered.message}")

        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        content = doc.get("content", {})
        title = content.get("title", {}).get("title", doc.get("documentId", ""))
        body_html = convert(rendered.value["content"])

        html = render_viewer_html(
            title=title,
            document_id=doc.get("documentId", ""),
            schema_ref=doc.get("schemaRef", ""),
            tags=doc.get("tags", []),
            updated_at=doc.get("updatedAt", ""),
            body_html=body_html,
        )

        try:
            self._documents.write_text(output_path, html)
        except OSError as e:
            return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")

        return Ok({"path": output_path, "content": html})

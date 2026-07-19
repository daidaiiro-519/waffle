"""render handoff template — Handoff document.jsonを、確定済みの固定HTMLテンプレート
（Pattern G）へ描画するapplication use case（uc-render-handoff-template）。

宣言的なx-render機構では表現できない固定デザインを、Handoff専用の薄いusecaseとして
実現する（evidence-based-scope、2件目の実例が出るまで汎用フレームワーク化しない）。
読み取り専用の投影であり、Handoff集約自身の状態・内容は変更しない。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.application.services.document_loading import load_document
from waffle.domain.services.completion_image_layout import compute_layout
from waffle.domain.services.handoff_html_template import render_handoff_html
from waffle.shared.result import Err, Ok, Result

_HANDOFF_SCHEMA_REF = "HandoffSchema/v1"


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def _count_by_advisor(design_viewpoints: list[dict], implementation_viewpoints: list[dict]) -> list[dict]:
    counts: dict[str, dict[str, int]] = {}
    for item in design_viewpoints:
        counts.setdefault(item["advisor"], {"design": 0, "impl": 0})["design"] += 1
    for item in implementation_viewpoints:
        counts.setdefault(item["advisor"], {"design": 0, "impl": 0})["impl"] += 1
    return [{"advisor": advisor, **c} for advisor, c in counts.items()]


class RenderHandoffTemplate:
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, document_path: str, output_path: str) -> Result[dict]:
        loaded = load_document(self._documents, document_path)
        if isinstance(loaded, Err):
            return loaded
        doc = loaded.value

        if doc.get("schemaRef") != _HANDOFF_SCHEMA_REF:
            return _err("WRONG_SCHEMA_REF", f"schemaRef が {_HANDOFF_SCHEMA_REF} ではありません")

        content = doc.get("content", {})
        completion_image = content.get("completionImage")
        if not completion_image:
            return _err("MISSING_COMPLETION_IMAGE", "completionImage ブロックがありません")

        title = content.get("title", {}).get("title", "")
        spec_ref = content.get("specRef", {}).get("specRef", "")
        design_viewpoints = content.get("designViewpoints", {}).get("items", [])
        implementation_viewpoints = content.get("implementationViewpoints", {}).get("items", [])
        constraints = content.get("constraints", {}).get("items", [])
        usage_examples = content.get("usageExamples", {}).get("items", [])

        layout = compute_layout(completion_image["layers"], completion_image["relationships"])
        review_counts = _count_by_advisor(design_viewpoints, implementation_viewpoints)
        handoff_kind = content.get("handoffKind", {}).get("value", "specToImplementation")

        html = render_handoff_html(
            title=title,
            document_id=doc["documentId"],
            spec_ref=spec_ref,
            layout=layout,
            layers=completion_image["layers"],
            review_counts=review_counts,
            design_viewpoints=design_viewpoints,
            implementation_viewpoints=implementation_viewpoints,
            constraints=constraints,
            handoff_kind=handoff_kind,
            usage_examples=usage_examples,
        )

        try:
            self._documents.write_text(output_path, html)
        except OSError as e:
            return _err("WRITE_ERROR", f"書き込みに失敗しました: {e}")

        return Ok({"path": output_path, "content": html})

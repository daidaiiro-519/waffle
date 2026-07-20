"""document graph ローカルサーバー — uc-render-document-graphのもう1つのfront-door。

CLI（waffle render-document-graph）と同じRenderDocumentGraph usecaseを、
GETのたびに呼び直すだけの薄いHTTPアダプタ。都度フルスキャン・永続インデックス
なしという既存設計をそのまま踏襲するため、新しい状態管理は持たない——ブラウザの
再読み込みだけで常に最新のグラフが返る（「レンダリングし忘れ」への対処、
ユーザーフィードバック「画面から更新すれば常に最新にできる仕組みにできないか」）。
design-shareのconsole_server.pyと同じ方針で127.0.0.1限定。
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from waffle.adapters.outbound.fs import FsDocumentRepository
from waffle.application.usecases.render_document_graph import RenderDocumentGraph
from waffle.shared.result import Ok


def _make_handler(directory: str, output_path: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server の規約に合わせる)
            if self.path not in ("/", ""):
                self.send_response(404)
                self.end_headers()
                return
            result = RenderDocumentGraph(FsDocumentRepository()).run(directory, output_path)
            if isinstance(result, Ok):
                body = result.value["content"].encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = result.message.encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # 標準出力を静かにする
            pass

    return Handler


def serve(directory: str, output_path: str, port: int = 4173) -> ThreadingHTTPServer:
    """127.0.0.1:port でリッスンするHTTPServerを作って返す（起動はserve_foreverを呼ぶ側が行う）。"""
    handler = _make_handler(directory, output_path)
    return ThreadingHTTPServer(("127.0.0.1", port), handler)

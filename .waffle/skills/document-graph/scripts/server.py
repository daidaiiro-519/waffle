"""server.py — document-graph Skillのローカルサーバー（127.0.0.1限定）。

design-shareのconsole_server.pyと同じ立て付け（標準ライブラリのみ、localhost限定）。
GET / のたびに config.py → graph_index.py → treemap_layout.py →
graph_viewer_html_template.py の一連を再実行して最新のグラフHTMLを返す（永続
インデックスを持たない・ブラウザの再読み込みだけで常に最新になる）。

GET /files/{alias}/{relpath} は、契約準拠のMD/HTMLファイルそのものを配信する
（sources/{alias}/ シムリンク経由でディスクから読むだけ）。

GET /preview/{alias}/{relpath} は、MD形式ソースを「全体」タブ用にCSS整形済みHTML
へその場変換して返す（Waffle本体のuc-render-document-viewerと同じ
markdown_to_html.convert + 同一ビューアCSSで、document.jsonには一切依存しない汎用
変換。HTML形式ソースは既にCSSが当たっているため、この変換ルートを経由せず/filesを
直接iframe参照する）。
"""
from __future__ import annotations

import os
import posixpath
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as config_mod  # noqa: E402
import graph_index  # noqa: E402
from graph_viewer_html_template import render_graph_html  # noqa: E402
from markdown_to_html import convert as convert_md  # noqa: E402
from md_preview_html_template import render_preview_html  # noqa: E402

HOST = "127.0.0.1"
DEFAULT_PORT = 4173
_FILES_PREFIX = "/files/"
_PREVIEW_PREFIX = "/preview/"


def build_page(config_path: Path = config_mod.DEFAULT_CONFIG_PATH, sources_dir: Path = config_mod.DEFAULT_SOURCES_DIR) -> str:
    config = config_mod.load_config(config_path)
    config_mod.sync_symlinks(config, sources_dir)
    graph = graph_index.scan_sources(sources_dir, config["sources"])
    return render_graph_html(
        graph, warnings=graph["warnings"], files_base_url=_FILES_PREFIX, preview_base_url=_PREVIEW_PREFIX
    )


def build_preview(target: Path, node_id: str) -> str:
    text = target.read_text(encoding="utf-8")
    frontmatter, body = graph_index.parse_md(text)
    title = frontmatter.get("title") or node_id
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    description = frontmatter.get("description", "")
    body_html = convert_md(body)
    return render_preview_html(
        title=title, document_id=node_id, tags=tags, description=description, body_html=body_html,
        schema_ref=frontmatter.get("schemaRef", ""), updated_at=frontmatter.get("updatedAt", ""),
    )


def _make_handler(config_path: Path, sources_dir: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server の規約に合わせる)
            parsed_path = urllib.parse.urlparse(self.path).path
            if parsed_path in ("/", ""):
                self._serve_graph()
            elif parsed_path.startswith(_FILES_PREFIX):
                self._serve_file(parsed_path[len(_FILES_PREFIX):])
            elif parsed_path.startswith(_PREVIEW_PREFIX):
                self._serve_preview(parsed_path[len(_PREVIEW_PREFIX):])
            else:
                self.send_response(404)
                self.end_headers()

        def _serve_graph(self) -> None:
            try:
                body = build_page(config_path, sources_dir).encode("utf-8")
            except Exception as e:  # スキャン失敗を握りつぶさず表面化する
                self._send_text(500, f"グラフの生成に失敗しました: {e}")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _resolve_source_file(self, rel: str) -> Path | None:
            # sources_dir配下は各alias自体がシムリンクなので実体はsources_dir外に
            # あるのが正常（論点1のフォルダ正規化）。よってtarget.resolve()での
            # 封じ込め判定はしない。トラバーサル対策は正規化パスの".."/絶対パス
            # 拒否と、宣言済みaliasのみを1階層目として許可することで行う。
            rel = urllib.parse.unquote(rel)
            norm = posixpath.normpath(rel)
            if norm.startswith("..") or norm.startswith("/") or norm in (".", ""):
                return None
            alias = norm.split("/", 1)[0]
            if not (sources_dir / alias).is_symlink():
                return None
            target = sources_dir / norm
            if not target.exists() or not target.is_file():
                return None
            return target

        def _serve_file(self, rel: str) -> None:
            target = self._resolve_source_file(rel)
            if target is None:
                self.send_response(404)
                self.end_headers()
                return
            content_type = "text/html; charset=utf-8" if target.suffix == ".html" else "text/markdown; charset=utf-8"
            self._send_bytes(200, content_type, target.read_bytes())

        def _serve_preview(self, rel: str) -> None:
            target = self._resolve_source_file(rel)
            if target is None or target.suffix != ".md":
                self.send_response(404)
                self.end_headers()
                return
            try:
                html = build_preview(target, target.stem).encode("utf-8")
            except Exception as e:  # 変換失敗を握りつぶさず表面化する
                self._send_text(500, f"プレビューの生成に失敗しました: {e}")
                return
            self._send_bytes(200, "text/html; charset=utf-8", html)

        def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_text(self, status: int, text: str) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:  # 標準出力を静かにする
            pass

    return Handler


def make_server(
    port: int = DEFAULT_PORT,
    config_path: Path = config_mod.DEFAULT_CONFIG_PATH,
    sources_dir: Path = config_mod.DEFAULT_SOURCES_DIR,
) -> ThreadingHTTPServer:
    handler = _make_handler(config_path, sources_dir)
    return ThreadingHTTPServer((HOST, port), handler)


def serve(port: int = DEFAULT_PORT) -> None:
    server = make_server(port)
    print(f"document-graph: http://{HOST}:{port}/  (Ctrl+Cで終了)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    serve()

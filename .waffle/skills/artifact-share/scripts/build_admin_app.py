"""管理画面の本体を組み立てる。

材料はすべてこの skill が持つ。以前はモック（docs/artifact-share/ui/）から
行番号でマークアップを切り出していたが、モックは描き換えるためのものなので、
描き換えるたびにここが壊れた（実際に壊れた）。

いま両者が共有するのは references/templates/app.css だけ。揃えるべきは色・余白・
部品であって、DOMの並びではない。マークアップは互いに持ち、スタイルだけを配る。

app.css の規範値は DESIGN.md のフロントマターにあり、モックへは
scripts/sync_styles.py が同じものを配る。
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PARTS = HERE / "app"
CSS = SKILL / "references" / "templates" / "app.css"
OUT = SKILL / "references" / "templates" / "upload-app.html"


def part(name: str) -> str:
    return (PARTS / name).read_text(encoding="utf-8")


def shared_css() -> str:
    """共有のスタイル。先頭の説明は運ばない（出どころはこのビルドが語る）。"""
    css = CSS.read_text(encoding="utf-8")
    return css[css.index("*/") + 2:].lstrip("\n") if css.startswith("/*") else css


body = "\n".join([
    '<div class="toast" id="toast" role="status" aria-live="polite">',
    '  <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.4l3.2 3.2L13 4.8"/></svg>',
    '  <span id="toast-text"></span>',
    "</div>",
    part("app-login.html"),
    part("app-page.html"),
    part("app-members.html"),
    part("app-projects.html"),
    part("app-dialogs.html"),
    part("app-admin-dialogs.html"),
])

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    "<title>artifactshare</title>\n<style>\n"
    + shared_css()
    + part("app-extra.css")
    + "</style>\n</head>\n<body>\n"
    + body
    + "\n<script>\n" + part("app.js") + "</script>\n</body>\n</html>\n",
    encoding="utf-8")

print(f"{OUT} を作りました（{OUT.stat().st_size // 1024} KB）")

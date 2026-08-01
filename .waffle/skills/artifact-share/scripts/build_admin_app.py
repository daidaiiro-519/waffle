"""管理画面の本体を組み立てる。

見た目は、合意済みのモック（main.html / admin.html）の作りをそのまま使う。
違うのは中身の出どころだけで、作り物のデータの代わりに受け口を呼ぶ。

スタイルとマークアップをモックから写すのは、両者が別物に育つのを防ぐため。
描く処理は作り直す（モックのものは手元の配列を描いていて、待ち・失敗・
入り直しの扱いを持たないため）。
"""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
UI = SKILL.parents[2] / "docs" / "artifact-share" / "ui"
OUT = SKILL / "references" / "templates" / "upload-app.html"
PARTS = HERE / "app"


def section(text: str, start: int, end: int) -> str:
    """1始まりの行番号で切り出す（両端を含む）。"""
    return "\n".join(text.splitlines()[start - 1:end])


admin = (UI / "admin.html").read_text(encoding="utf-8")
main = (UI / "main.html").read_text(encoding="utf-8")

# スタイル: 管理者のモックのもの（土台＋管理者の面）をそのまま使う
css = admin.split("<style>", 1)[1].split("</style>", 1)[0]

# 本文: 投稿者の面はアーティファクトのモックから、
#       メンバーの面と対話は管理者のモックから写す
main_page = section(main, 269, 408)          # <div class="page"> … </div>
main_dialogs = section(main, 411, 582)       # 対話とお知らせ
members = section(admin, 343, 355)           # メンバーの面
admin_dialogs = section(admin, 359, 428)     # 引き継ぎ・招く・外す

# 投稿者の面へ、管理者の面を差し込む
projects_view = (PARTS / "app-projects.html").read_text(encoding="utf-8")
view, _, dialogs = projects_view.partition("<!-- ══ プロジェクトを作る ══ -->")
page = main_page.replace("\n</div>", "\n" + members + "\n" + view + "\n</div>")
admin_dialogs += "\n<!-- ══ プロジェクトを作る ══ -->" + dialogs

body = "\n".join([
    (PARTS / "app-login.html").read_text(encoding="utf-8"),
    page,
    main_dialogs,
    admin_dialogs,
])

# お知らせ（toast）が二重にならないよう、管理者側のものは落とす
body = re.sub(r'<div class="toast" id="toast".*?</div>\n', "", body, count=1, flags=re.S)
body = ('<div class="toast" id="toast" role="status" aria-live="polite">\n'
        '  <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.4l3.2 3.2L13 4.8"/></svg>\n'
        '  <span id="toast-text"></span>\n</div>\n') + body

extra_css = (PARTS / "app-extra.css").read_text(encoding="utf-8")
js = (PARTS / "app.js").read_text(encoding="utf-8")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
    "<title>artifactshare</title>\n<style>"
    + css + extra_css
    + "</style>\n</head>\n<body>\n"
    + body
    + "\n<script>\n" + js + "</script>\n</body>\n</html>\n",
    encoding="utf-8")

print(f"{OUT} を作りました（{OUT.stat().st_size // 1024} KB）")

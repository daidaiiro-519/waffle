"""test_manage.py の私物の足場を、足場のファイルへ寄せる。

同じものが2つあると、片方だけが失敗を作れる状態になる。実際に一度起きている。
"""
from __future__ import annotations

import pathlib
import re

P = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests/test_manage.py")

t = P.read_text(encoding="utf-8")

# 私物の定義を落とす
for pattern in (
    r"\nNOW = 1_700_000_000\n",
    r'\nME = Caller\("publisher-1"\)\n',
    r'def setup\(keys=None\):\n    """公開済みのものが1件ある状態を作り、依存と公開の結果を返す。"""\n(?:.*?\n)*?    return deps, result\n\n\n',
    r'def meta_of\(deps, artifact_id\):\n    return json\.loads\(deps\.store\.get\(f"meta/\{artifact_id\}\.json"\)\)\n\n\n',
    r'def with_project\(scope, owner=None\):\n    """プロジェクトが1つある状態を作る。既定では自分（ME）が作ったもの。"""\n(?:.*?\n)*?    return deps, r, p\.project_id\n\n\n',
):
    new = re.sub(pattern, "\n" if pattern.startswith(r"\n") else "", t, count=1)
    if new == t:
        raise SystemExit(f"見つかりません: {pattern[:60]}")
    t = new

# 中身が空の見出しだけが残っている箇所を落とす
t = re.sub(r"\n# ── (本人以外は触れない|差し替え) ─+\n(?=\n\n# ──|\n\ndef )", "", t)

# 足場から取り込む
t = t.replace("from manage_setup import HTML  # noqa: E402",
              "from manage_setup import (  # noqa: E402\n"
              "    HTML, ME, NOW, meta_of, setup, with_project,\n"
              ")", 1)

P.write_text(t, encoding="utf-8")
print("寄せた: test_manage.py")

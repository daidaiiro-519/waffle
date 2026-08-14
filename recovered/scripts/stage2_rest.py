"""残る4ファイルの私物の足場を、足場のファイルへ寄せる。"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")


def edit(rel: str, drops: list[str], import_old: str, import_new: str) -> None:
    p = TESTS / rel
    t = p.read_text(encoding="utf-8")
    for pattern in drops:
        new = re.sub(pattern, "", t, count=1)
        if new == t:
            raise SystemExit(f"{rel} に見つかりません: {pattern[:70]}")
        t = new
    if import_old:
        if import_old not in t:
            raise SystemExit(f"{rel} に見つかりません: {import_old}")
        t = t.replace(import_old, import_new, 1)
    # 中身が空の見出しだけが残っている箇所
    t = re.sub(r"\n# ── [^\n]+ ─+\n(?=\n\n# ──|\n\ndef |\Z)", "", t)
    p.write_text(t, encoding="utf-8")
    print("寄せた:", rel)


# ── 引き継ぎ ───────────────────────────────────────────
edit("test_transfer.py",
     [r'\nX = Caller\("publisher-x"\)\nY = Caller\("publisher-y"\)\nADMIN = Caller\("admin-1", is_admin=True\)\n',
      r'def setup\(\):\n    """XがAを公開しており、Yも招かれている状態を作る。"""\n(?:.*?\n)*?    return deps, result\n\n\n',
      r'def meta_of\(deps, artifact_id\):\n    return json\.loads\(deps\.store\.get\(f"meta/\{artifact_id\}\.json"\)\)\n\n\n'],
     "from manage_setup import HTML  # noqa: E402",
     "from manage_setup import HTML, meta_of  # noqa: E402\n"
     "from transfer_setup import ADMIN, X, Y, setup  # noqa: E402")

# ── プロジェクト ───────────────────────────────────────
edit("test_projects.py",
     [r'\nADMIN = Caller\("admin-1", is_admin=True\)\n',
      r'def setup\(\):\n(?:.*?\n)*?    return main\.Connections\(\n(?:.*?\n)*?    \)\n\n\n',
      r'def index_of\(deps, project_id\):\n(?:.*?\n)*?\n\n',
      r'def listing_of\(deps, project_id\):\n(?:.*?\n)*?\n\n',
      r'def owned\(deps, scope="PERSONAL"\):\n(?:.*?\n)*?\n\n',
      # 誰からも呼ばれていない残骸
      r'def artifact\(deps, artifact_id, name, owner=X, status="active"\):\n(?:.*?\n)*?\n\n',
      r'def manage_assign\(deps, caller, artifact_id, project_id\):\n(?:.*?\n)*?\Z'],
     "", "")

# ── 名簿 ───────────────────────────────────────────────
edit("test_publishers.py", [], "", "")

# ── コメント ───────────────────────────────────────────
edit("test_comments.py",
     [r'\nME = Caller\("publisher-1"\)\n', r'\nADMIN = Caller\("admin-1", is_admin=True\)\n'],
     "from manage_setup import HTML  # noqa: E402",
     "from manage_setup import ADMIN, HTML, ME  # noqa: E402")

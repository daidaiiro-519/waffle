#!/usr/bin/env python3
"""共有のスタイルを、モックと管理画面へ配り直す。

揃えるべきは色・余白・部品であって、DOMの並びではない。だから共有するのは
references/templates/app.css だけにして、マークアップは互いに持たない。

モックは単体で開ける必要がある（外部への参照をひとつも持たない約束）ので、
参照ではなく差し込みで配る。差し込み口は各モックの <style> の先頭にあり、
そこを直接編集しない——次にこれを走らせたときに消える。

実行:  python3 scripts/sync_styles.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
CSS = SKILL / "references" / "templates" / "app.css"
UI = SKILL.parents[2] / "docs" / "artifact-share" / "ui"

TARGETS = ["main.html", "admin.html", "login.html", "project.html"]
BEGIN = "  /* ══ 共有のスタイル（app.css から配られる。ここを直接編集しない） ══ */"
END = "  /* ══ 共有のスタイルここまで ══ */"


def main() -> int:
    shared = CSS.read_text(encoding="utf-8").rstrip("\n")
    # ファイル先頭の説明はモックへ運ばない（出どころはこの差し込み口が語る）
    if shared.startswith("/*"):
        shared = shared[shared.index("*/") + 2:].lstrip("\n")

    changed = []
    for name in TARGETS:
        path = UI / name
        s = path.read_text(encoding="utf-8")
        if BEGIN not in s or END not in s:
            print(f"{name}: 差し込み口がありません", file=sys.stderr)
            return 1
        head, _, rest = s.partition(BEGIN)
        _, _, tail = rest.partition(END)
        new = head + BEGIN + "\n" + shared + "\n" + END + tail
        if new != s:
            path.write_text(new, encoding="utf-8")
            changed.append(name)

    print("配りました:", ", ".join(changed) if changed else "（変更なし）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

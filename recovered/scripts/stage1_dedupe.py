"""段1：重複を消し、失われる検証だけをシナリオ側へ寄せ、空疎な2件を直す。

消す前に、対応するシナリオ側のテストが実在することを1件ずつ確かめてある。
"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")


def drop(rel: str, names: list[str]) -> None:
    """名前で指したテスト関数を丸ごと落とす。"""
    p = TESTS / rel
    t = p.read_text(encoding="utf-8")
    for name in names:
        m = re.search(rf"^def {re.escape(name)}\(\):\n(?:.*?\n)*?(?=^def |^# ──|\Z)",
                      t, re.M)
        if not m:
            raise SystemExit(f"{rel} に見つかりません: {name}")
        t = t[:m.start()] + t[m.end():]
    p.write_text(t, encoding="utf-8")
    print(f"消した: {rel} から {len(names)}件")


def patch(rel: str, pairs: list[tuple[str, str]]) -> None:
    p = TESTS / rel
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in t:
            raise SystemExit(f"{rel} に見つかりません:\n{old}")
        t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("直した:", rel)


# ── 先に、消すことで失われる検証をシナリオ側へ寄せる ────────
EXPORT = "application/acceptance/test_uc_export_artifact.py"

patch(EXPORT, [
    # 表示名。中身だけでなく、何という名前で公開されたものかも返る
    ("    assert got.content == HTML\n    assert len(got.comments) == 3",
     '    assert got.content == HTML\n'
     '    assert got.name == "検索基盤の選定"\n'
     '    assert len(got.comments) == 3'),
    # 閲覧トークンが含まれないことを、欄の名前ごと見る。
    # 表示の形（repr）だけを見ると、欄名が変わったときに素通りする
    ('    assert r.token not in repr(got)\n    assert not hasattr(got, "token")',
     '    got = json.dumps(asdict(got), ensure_ascii=False)\n'
     '    assert r.token not in got\n'
     '    assert "token" not in got      # 値だけでなく欄の名前も見る'),
])

t = (TESTS / EXPORT).read_text(encoding="utf-8")
if "from dataclasses import asdict" not in t:
    t = t.replace("import json\n", "import json\nfrom dataclasses import asdict\n", 1)
    (TESTS / EXPORT).write_text(t, encoding="utf-8")
    print("取り込みを足した:", EXPORT)

# 何度取り出しても同じものが返ることは、既に別のシナリオが持っている
# （test_何度取り出しても同じものが返る）ので、寄せる必要は無い

# ── 重複を消す ────────────────────────────────────────
drop("test_comments.py", [
    "test_公開が止まっていても読める",
    "test_読んでも何も変わらない",
    "test_中身とコメントがまとめて返る",
    "test_取り出しても何も変わらない",
    "test_公開が止まっていても取り出せる",
    "test_取り出したものに閲覧トークンは含まれない",
    "test_他人のものは取り出せない",
])

drop("test_transfer.py", [
    "test_管理者は他人のものも一覧できる",
    "test_管理者は他人のものを公開停止_再開できる",
    "test_管理者でも他人の中身は差し替えられない",
    "test_第三者には見つからないものとして拒む",
    "test_移した先が手入れできるようになる",
])

# 契約表の9ケースが上位互換に覆っており、取りこぼし検知まで持つ
drop("test_publish.py", [
    "test_metaタグを読み取る",
    "test_metaタグが無ければタイトルだけ拾う",
    "test_外部への参照を数える",
    "test_data_URIは外部への参照に数えない",
])

# ── 空疎な2件を直す ──────────────────────────────────
# 壊れた記録を作らずに「壊れていない」を確かめており、数え上げを
# return 0 に変えても落ちない
drop("test_manage.py", ["test_読めるものだけなら件数は0"])

# 置かれた個数は、順序という確かめたい性質ではない。
# 無関係な書き込みが1つ増えるだけで落ち、順序の逆転は前段が捕まえている
patch("test_publish.py", [
    ("    # 中身・閲覧画面・雛形の版・記録の4つは置き終えている（到達はできない）\n"
     "    assert len(store.objects) == 4\n", ""),
])

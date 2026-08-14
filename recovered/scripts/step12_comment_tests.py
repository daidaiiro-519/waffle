"""検証を、業務の語彙で受け取る形へ追随させる。確かめている中身は変えない。"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")

# 外向きの綴り → 業務の語彙の属性名
FIELD = {
    "author": "author", "body": "body", "kind": "kind", "postedAt": "posted_at",
    "parentId": "parent_id", "decision": "verdict", "id": "id",
}

TARGETS = [
    "application/acceptance/test_uc_read_comments.py",
    "application/integration/test_uc_read_comments.py",
    "application/acceptance/test_uc_export_artifact.py",
]

for rel in TARGETS:
    p = TESTS / rel
    t = original = p.read_text(encoding="utf-8")
    for outward, attr in FIELD.items():
        t = re.sub(rf'\[\s*"{outward}"\s*\]', f".{attr}", t)
    if t != original:
        p.write_text(t, encoding="utf-8")
        print("直した:", rel)

# 「保存されている形のまま返る」は、もう成り立たない約束。
# 何を確かめたいのか（欄が揃っていること）は変えずに、宣言し直す
p = TESTS / "test_comments.py"
t = p.read_text(encoding="utf-8")
t = t.replace(
    'def test_保存されている形のまま返る():\n'
    '    """表示用に整えるのは画面側。ここで別の呼び名へ置き換えない"""\n'
    '    deps, aid = setup()\n'
    '    post(deps, aid, 1700000001, "田中", "本文")\n'
    '\n'
    '    c = build(deps, ReadComments).run(ME, aid).comments[0]\n'
    '    assert set(c) >= {"kind", "author", "decision", "body", "parentId", "postedAt"}',
    'def test_業務の語彙で返り欠けが無い():\n'
    '    """外の綴りへ直すのは受け口の仕事。ここが返すのは業務の語彙。\n'
    '\n'
    '    判定だけは保管も画面も decision と呼び、業務は判定と呼ぶ。既に書かれた\n'
    '    記録の欄名を変えられないための食い違いで、対応は受け口が宣言する。\n'
    '    """\n'
    '    deps, aid = setup()\n'
    '    post(deps, aid, 1700000001, "田中", "本文")\n'
    '\n'
    '    c = build(deps, ReadComments).run(ME, aid).comments[0]\n'
    '\n'
    '    assert (c.kind, c.author, c.body) == ("comment", "田中", "本文")\n'
    '    assert c.verdict == "comment"      # 添えなければ、ただの意見\n'
    '    assert c.parent_id is None\n'
    '    assert c.posted_at\n'
    '    assert c.id == "1700000001-abcd1234"', 1)
t = t.replace('    assert [c["author"] for c in got.comments] == ["田中", "佐藤"]',
              '    assert [c.author for c in got.comments] == ["田中", "佐藤"]', 1)
p.write_text(t, encoding="utf-8")
print("直した: test_comments.py")

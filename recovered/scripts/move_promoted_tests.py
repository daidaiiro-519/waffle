"""昇格した7件の検証を、シナリオに束ねられるファイルへ移す。

先頭の宣言行が突き合わせのキー、続くGiven/When/Thenは仕様の文言の一字一句の写し。
実装は元のまま持ち込み、その場の呼び方へだけ合わせる。
"""
from __future__ import annotations

import ast
import json
import pathlib
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
TESTS = pathlib.Path(CWD) / ".waffle/skills/artifact-share/tests"
UC = ".waffle/documents/specs/bc-artifact-share/subdomain/sd-artifact-sharing/usecase"


def gherkin(spec: str, block: str, name: str) -> str:
    """仕様の筋書きを、そのままdocstringの本文にする。"""
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", f"{UC}/{spec}.json", "--blockKey", block, "--expression", "scenarios"],
        capture_output=True, text=True, cwd=CWD)
    for s in json.loads(r.stdout)["value"]:
        if s["name"] == name:
            return s["gherkin"]
    raise SystemExit(f"{spec} に筋書きがありません: {name}")


def drop(rel: str, names: list[str]) -> None:
    p = TESTS / rel
    src = p.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    spans = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name in names:
            end = n.end_lineno
            while end < len(lines) and lines[end].strip() == "":
                end += 1
            spans.append((n.lineno - 1, end))
    if len(spans) != len(names):
        raise SystemExit(f"{rel}: {len(spans)}/{len(names)} しか見つかりません")
    for start, end in sorted(spans, reverse=True):
        del lines[start:end]
    p.write_text("".join(lines), encoding="utf-8")
    print(f"  元から外した: {rel}（{len(names)}件）")


def append(rel: str, spec: str, block: str, name: str, note: str, body: str) -> None:
    p = TESTS / rel
    t = p.read_text(encoding="utf-8").rstrip("\n")
    doc = gherkin(spec, block, name)
    tail = f'\n\n    {note}\n    ' if note else "\n    "
    t += (f'\n\n\ndef test_{name}():\n'
          f'    """\n    ' + doc.replace("\n", "\n    ") + tail + '"""\n' + body + "\n")
    p.write_text(t, encoding="utf-8")
    print(f"  足した: {rel} ← {name}")


# ── コメントの読み出し ────────────────────────────────
append("application/acceptance/test_uc_read_comments.py", "uc-read-comments",
       "acceptanceScenarios", "管理者は他人のものも読める",
       "拒む側の筋書きは既にあるが、許す側が無かった。",
       '    deps, r = setup()\n'
       '    _post(deps, r.artifact_id, 1_700_000_010, "田中", "意見")\n'
       '\n'
       '    assert len(_read(deps, ADMIN, r.artifact_id)) == 1')

append("application/acceptance/test_uc_read_comments.py", "uc-read-comments",
       "acceptanceScenarios", "読めない記録があっても残りが返る",
       "黙って落とすと、投稿者は「これで全部だ」と思い込む。",
       '    deps, r = setup()\n'
       '    _post(deps, r.artifact_id, 1_700_000_010, "田中", "読める")\n'
       '    deps.store.put(f"comments/{r.artifact_id}/1700000020-broken.json",\n'
       '                   "{壊れている", "application/json")\n'
       '    _post(deps, r.artifact_id, 1_700_000_030, "佐藤", "これも読める")\n'
       '\n'
       '    got = ReadComments(deps.artifacts, deps.comments).run(ME, r.artifact_id)\n'
       '\n'
       '    assert [c.author for c in got.comments] == ["田中", "佐藤"]\n'
       '    assert got.unreadable == 1')

# ── プロジェクトへの出し入れ ──────────────────────────
append("application/acceptance/test_uc_assign_to_project.py", "uc-assign-to-project",
       "acceptanceScenarios", "上限を超えてプロジェクトへ加えられない",
       "閲覧の面は先頭から決まった数しか見ない。書き手が黙って超えると、\n"
       "    投稿者には成功が返り、閲覧者だけが開けない状態になる。",
       '    deps, r, _ = with_project("SHARED")\n'
       '    ids = []\n'
       '    for i in range(MAX_PROJECTS + 1):\n'
       '        p = build(deps, CreateProject).run(ME, f"まとめ{i}", "SHARED")\n'
       '        ids.append(p.project_id)\n'
       '\n'
       '    for pid in ids[:MAX_PROJECTS]:\n'
       '        _assign(deps, ME, r.artifact_id, pid)\n'
       '\n'
       '    with pytest.raises(ManageError) as x:\n'
       '        _assign(deps, ME, r.artifact_id, ids[-1])\n'
       '\n'
       '    assert x.value.code == "TOO_MANY_PROJECTS"\n'
       '    assert len(meta_of(deps, r.artifact_id)["projects"]) == MAX_PROJECTS')

# ── 中身の差し替え ────────────────────────────────────
append("application/acceptance/test_uc_replace_content.py", "uc-replace-content",
       "acceptanceScenarios", "空の中身には差し替えられない", "",
       '    deps, r = setup()\n'
       '\n'
       '    with pytest.raises(ManageError) as x:\n'
       '        build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, "   ")\n'
       '\n'
       '    assert x.value.code == "EMPTY_CONTENT"\n'
       '    assert deps.store.get(f"p/{r.artifact_id}/content.html") == HTML')

# ── プロジェクトを作る ────────────────────────────────
append("application/acceptance/test_uc_create_project.py", "uc-create-project",
       "acceptanceScenarios", "想定外の共有の別では作らない", "",
       '    deps = setup()\n'
       '\n'
       '    with pytest.raises(ProjectError) as x:\n'
       '        build(deps, CreateProject).run(X, "まとめ", "EVERYONE")\n'
       '\n'
       '    assert x.value.code == "SCOPE_REQUIRED"')

# ── 自分のものを見渡す ────────────────────────────────
append("application/acceptance/test_uc_list_my_artifacts.py", "uc-list-my-artifacts",
       "acceptanceScenarios", "差し替えの区切りはコメントの件数に数えない",
       "区切りは印であって、誰かの反応ではない。",
       '    deps, r = setup()\n'
       '    _comment(deps, r.artifact_id, 1_700_000_010, "田中")\n'
       '    _comment(deps, r.artifact_id, 1_700_000_020, "佐藤")\n'
       '\n'
       '    build(deps, ReplaceArtifactContent).run(\n'
       '        ME, r.artifact_id, HTML.replace("本文", "直した"))\n'
       '\n'
       '    assert _rows(deps)[0].comments == 2')

# ── 投稿者を招く（操作保証） ──────────────────────────
append("application/integration/test_uc_invite_publisher.py", "uc-invite-publisher",
       "guaranteeScenarios", "招待が返す識別子は一覧のものと揃っている",
       "宛先で入る設定のため、名簿の識別子は宛先そのものではない。",
       '    deps, _ = setup()\n'
       '\n'
       '    invited = build(deps, InvitePublisher).run(\n'
       '        "invite", ADMIN, email="new@example.com")\n'
       '    listed = {row.id for row in build(deps, ListPublishers).run(ADMIN)}\n'
       '\n'
       '    assert invited.publisher_id in listed')

# ── 元から外す ────────────────────────────────────────
drop("application/unit/test_comments.py",
     ["test_管理者は他人のものも読める", "test_読めない記録があっても残りが返る"])
drop("application/unit/test_manage.py",
     ["test_上限を超えてプロジェクトへ加えられない", "test_空の中身には差し替えられない",
      "test_差し替えの区切りはコメントの件数に数えない"])
drop("application/unit/test_projects.py", ["test_想定外の共有の別では作らない"])
drop("application/unit/test_publishers.py", ["test_招待が返す識別子は一覧のものと揃っている"])

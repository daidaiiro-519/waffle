"""検証の側を、新しい形へ追随させる。確かめている中身は変えない。"""
from __future__ import annotations

import pathlib

SKILL = pathlib.Path("/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share")
TESTS = SKILL / "tests"


def patch(rel: str, pairs: list[tuple[str, str]], count: int = 1) -> None:
    path = TESTS / rel
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"{rel} に見つかりません:\n{old}")
        text = text.replace(old, new, count)
    path.write_text(text, encoding="utf-8")
    print("直した:", rel)


# 決まった値を返す発行の口。検証では乱数を使わない（テスト規約の必須）
FAKE = '''

class FakeIdGenerator:
    """決まった値を順に返す発行の口。

    乱数を使うと、同じ検証が回ごとに別の値で走る。テスト規約が「時刻・乱数・
    ID生成は決定的な値に固定する」と定めているため、ここで固定する。
    """

    def __init__(self):
        self._n = 0

    def _next(self) -> str:
        self._n += 1
        return str(self._n)

    def new_artifact_id(self):
        from domain.value_objects.shared_artifact import ArtifactId
        return ArtifactId(("aaaaaaa" + self._next())[-8:])

    def new_project_id(self):
        from domain.value_objects.project import ProjectId
        return ProjectId(("ppppp" + self._next())[-6:])

    def new_view_token_id(self):
        from domain.value_objects.view_token import ViewTokenId
        return ViewTokenId(("ttttt" + self._next())[-6:])

    def new_view_token_secret(self) -> str:
        return "aaaa-bbbb-" + ("cccc" + self._next())[-4:]
'''

fakes = TESTS / "fakes.py"
text = fakes.read_text(encoding="utf-8")
if "FakeIdGenerator" not in text:
    fakes.write_text(text.rstrip() + "\n" + FAKE, encoding="utf-8")
    print("足した: fakes.py の FakeIdGenerator")

# ── 公開の口の組み立て ────────────────────────────────
patch("publish_setup.py", [
    ("        lambda _token: user,\n        lambda: NOW,\n    )",
     "        lambda _token: user,\n        lambda: NOW,\n        FakeIdGenerator(),\n    )"),
])
text = (TESTS / "publish_setup.py").read_text(encoding="utf-8")
if "FakeIdGenerator" not in text.split("def publishing")[0]:
    text = text.replace("from fakes import ", "from fakes import FakeIdGenerator, ", 1)
    (TESTS / "publish_setup.py").write_text(text, encoding="utf-8")
    print("直した: publish_setup.py の取り込み")

# ── 読み取れたものは、辞書ではなく型で受ける ──────────
patch("test_publish.py", [
    ('    assert d["documentId"] == "adr-search-backend"\n'
     '    assert d["docType"] == "DecisionRecord"\n'
     '    assert d["title"] == "検索基盤にPostgreSQLを採用する"   # titleタグより優先する\n'
     '    assert d["tags"] == ["backend", "search", "database"]\n'
     '    assert d["detected"] is True',
     '    assert d.document_id == "adr-search-backend"\n'
     '    assert d.doc_type == "DecisionRecord"\n'
     '    assert d.title == "検索基盤にPostgreSQLを採用する"   # titleタグより優先する\n'
     '    assert d.labels == ("backend", "search", "database")\n'
     '    assert d.detected is True'),
    ('    assert d["detected"] is False\n'
     '    assert d["title"] == "会員登録フローの離脱率メモ"\n'
     '    assert d["docType"] == ""',
     '    assert d.detected is False\n'
     '    assert d.title == "会員登録フローの離脱率メモ"\n'
     '    assert d.doc_type == ""'),
    ('    assert html_inspection.inspect_html(WITH_THREE_EXTERNAL)["externalRefs"] == 3\n'
     '    assert html_inspection.inspect_html(WITH_META)["externalRefs"] == 0',
     '    assert html_inspection.inspect_html(WITH_THREE_EXTERNAL).external_refs == 3\n'
     '    assert html_inspection.inspect_html(WITH_META).external_refs == 0'),
    ('    assert html_inspection.inspect_html(html)["externalRefs"] == 0',
     '    assert html_inspection.inspect_html(html).external_refs == 0'),
    ('    ids = {identifier.new_artifact_id() for _ in range(200)}\n'
     '    assert len(ids) == 200                      # 重ならない\n'
     '    for value in ids:\n'
     '        assert len(value) == 8',
     '    ids = {RandomIdGenerator().new_artifact_id().value for _ in range(200)}\n'
     '    assert len(ids) == 200                      # 重ならない\n'
     '    for value in ids:\n'
     '        assert len(value) == 8'),
])
text = (TESTS / "test_publish.py").read_text(encoding="utf-8")
if "RandomIdGenerator" not in text.split("def test_")[0]:
    text = text.replace("from domain.services import html_inspection",
                        "from adapters.outbound.random_identifier import RandomIdGenerator\n"
                        "from domain.services import html_inspection", 1)
    (TESTS / "test_publish.py").write_text(text, encoding="utf-8")
    print("直した: test_publish.py の取り込み")

# ── 発行は識別子を受け取る形になった ──────────────────
patch("domain/unit/test_agg_shared_artifact.py", [
    ('return view_token.issued(name, f"fingerprint-{name}",',
     'return view_token.issued(ViewTokenId("t-" + name), name,\n'
     '                            ViewTokenFingerprint(f"fingerprint-{name}"),'),
])
patch("domain/unit/test_agg_project.py", [
    ('return view_token.issued(name, "fingerprint-" + name,',
     'return view_token.issued(ViewTokenId("t-" + name), name,\n'
     '                            ViewTokenFingerprint("fingerprint-" + name),'),
])

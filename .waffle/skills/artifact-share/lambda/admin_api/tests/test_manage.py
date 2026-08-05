"""公開したあとの管理操作を、仕様の受け入れシナリオに沿って確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

これらの操作は、Cognitoで本人確認を通った投稿者がブラウザから呼ぶ。
手元のCLIは環境の構築だけを担い、ここには関わらない。

対象の仕様:
  uc-replace-content / uc-reissue-view-token / uc-suspend-artifact /
  uc-resume-artifact / uc-assign-to-project
"""

import main
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usecase_builder import build  # noqa: E402
from application.usecases.assign_artifact_to_project import AssignArtifactToProject  # noqa: E402
from application.usecases.control_project_access import ControlProjectAccess  # noqa: E402
from application.usecases.create_project import CreateProject  # noqa: E402
from application.usecases.list_my_artifacts import ListMyArtifacts  # noqa: E402
from application.usecases.publish_artifact import PublishArtifact  # noqa: E402
from application.usecases.replace_artifact_content import ReplaceArtifactContent  # noqa: E402
from application.usecases.resume_artifact import ResumeArtifact  # noqa: E402
from application.usecases.suspend_artifact import SuspendArtifact  # noqa: E402

from application.ports import Caller  # noqa: E402
from domain.shared_artifact import MAX_PROJECTS  # noqa: E402  # 旧 MAX_PROJECTS_PER_ARTIFACT
from domain.project import PERSONAL  # noqa: E402
from domain.project import SHARED  # noqa: E402
from shared.errors import ManageError  # noqa: E402


class FakeStore:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})

    def put(self, key, body, content_type):
        self.objects[key] = {"body": body, "content_type": content_type}

    def get(self, key):
        if key not in self.objects:
            raise KeyError(key)
        return self.objects[key]["body"]

    def list(self, prefix):
        return [k for k in sorted(self.objects) if k.startswith(prefix)]


class FakeKeyStore:
    def __init__(self, keys=None):
        self.keys = dict(keys or {})

    def put(self, key, value):
        self.keys[key] = value

    def get(self, key):
        if key not in self.keys:
            raise KeyError(key)
        return self.keys[key]


HTML = """<!doctype html><html><head>
<meta name="id" content="adr-x"><meta name="type" content="DecisionRecord">
<meta name="title" content="検索基盤の選定"><title>別</title></head><body>本文</body></html>"""

ME = Caller("publisher-1")
SOMEONE_ELSE = Caller("publisher-2")


def setup(keys=None):
    """公開済みのものが1件ある状態を作り、依存と公開の結果を返す。"""
    store = FakeStore()
    key_store = keys if keys is not None else FakeKeyStore()

    c = main.Connections(
            store=store, keys=key_store,
            identify=lambda _t: ME.id,
            wrapper_template="<html>{{アーティファクトID}}</html>",
            now=lambda: 1_700_000_000,
            viewer_domain="viewer.example.net",
        )
    result = build(c, PublishArtifact).run({"html": HTML, "authorization": "Bearer x"})
    deps = main.Connections(
        store=store, keys=key_store,
        now=lambda: 1_700_000_100,
        viewer_domain="viewer.example.net",
    )
    return deps, result


def meta_of(deps, artifact_id):
    return json.loads(deps.store.get(f"meta/{artifact_id}.json"))


# ── 本人以外は触れない ──────────────────────────────────

def test_他人が公開したものは存在しないものとして扱う():
    """存在そのものを漏らさないため、拒否ではなく見つからない扱いにする"""
    deps, r = setup()

    for call in (
        lambda: build(deps, ReplaceArtifactContent).run(SOMEONE_ELSE, r.artifact_id, HTML),
        lambda: build(deps, SuspendArtifact).run(SOMEONE_ELSE, r.artifact_id),
    ):
        with pytest.raises(ManageError) as x:
            call()
        assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_一覧には自分が公開したものだけが並ぶ():
    deps, mine = setup()
    other = dict(meta_of(deps, mine.artifact_id),
                 artifactId="zzzzzzzz", uploadedBy=SOMEONE_ELSE.id)
    deps.store.put("meta/zzzzzzzz.json", json.dumps(other), "application/json")

    ids = [row.artifact_id for row in build(deps, ListMyArtifacts).run(ME).artifacts]
    assert ids == [mine.artifact_id]


def test_一覧にトークンは含まれない():
    """トークンは発行の一度きり。一覧から取り出せてはならない"""
    deps, _ = setup()
    for row in build(deps, ListMyArtifacts).run(ME).artifacts:
        assert not hasattr(row, "token")


def test_一覧は公開中と停止中を区別して返す():
    deps, r = setup()
    assert build(deps, ListMyArtifacts).run(ME).artifacts[0].status == "PUBLISHED"
    build(deps, SuspendArtifact).run(ME, r.artifact_id)
    assert build(deps, ListMyArtifacts).run(ME).artifacts[0].status == "SUSPENDED"


# ── 差し替え ────────────────────────────────────────────

def test_差し替えてもURLとトークンの同一性が保たれる():
    """
    Scenario: 差し替えても共有URLは変わらない
    Given 共有アーティファクトAの共有URLが閲覧者へ渡されている
    When 中身を差し替える
    Then 共有URLは変わらない
    And 閲覧者は同じ共有URLで新しい中身を見られる
    """
    deps, r = setup()
    before = deps.keys.get(f"token:{r.artifact_id}")

    new_html = HTML.replace("本文", "直した本文")
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, new_html)

    assert deps.store.get(f"p/{r.artifact_id}/content.html") == new_html
    assert deps.keys.get(f"token:{r.artifact_id}") == before


def test_差し替えると前の中身は一部も残らない():
    """
    Scenario: 差し替えても中身は部分的に書き換わらない
    Given 共有アーティファクトAが公開されている
    When 新しい文書で中身を差し替える
    Then 中身は新しいものと完全に一致する
    And 差し替え前の中身の一部が残ることはない

    短いものへ差し替えて確かめる。上書きが部分的だと、前の中身の末尾が
    そのまま残る——長いもので確かめると、一致の検証を通ってしまう。
    """
    deps, r = setup()
    長い前の中身 = HTML.replace("本文", "本文" + "ここは消えるはず" * 20)
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, 長い前の中身)

    短い新しい中身 = HTML.replace("本文", "短い")
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, 短い新しい中身)

    置かれたもの = deps.store.get(f"p/{r.artifact_id}/content.html")
    assert 置かれたもの == 短い新しい中身
    assert "ここは消えるはず" not in 置かれたもの


def test_差し替えると区切りの記録が反応の並びに残る():
    """
    Scenario: 差し替えてもコメントが残る
    Given 共有アーティファクトAに3件のコメントが集まっている
    When 中身を差し替える
    Then 3件のコメントはいずれも残っている
    And 差し替えが行われた時点が区切りとして読み取れる
    """
    deps, r = setup()
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, HTML.replace("本文", "直した"))

    records = [json.loads(deps.store.get(k))
               for k in deps.store.list(f"comments/{r.artifact_id}/")]
    assert len(records) == 1
    assert records[0]["kind"] == "divider"


def test_公開が止まっているものは差し替えられない():
    deps, r = setup()
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, HTML)
    assert x.value.code == "NOT_PUBLISHED"


def test_空の中身には差し替えられない():
    deps, r = setup()
    with pytest.raises(ManageError) as x:
        build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, "   ")
    assert x.value.code == "EMPTY_CONTENT"


# ── 閲覧トークン ────────────────────────────────────────

def test_公開すると最初の1本が渡される():
    """相手ごとに増やせるが、公開した時点で1本は渡されている"""
    deps, r = setup()

    tokens = meta_of(deps, r.artifact_id)["viewTokens"]
    assert len(tokens) == 1
    assert r.token
    assert r.token not in str(tokens)

def test_停止すると開けなくなるがデータは残る():
    deps, r = setup()
    build(deps, SuspendArtifact).run(ME, r.artifact_id)

    assert deps.keys.get(f"token:{r.artifact_id}") == "DISABLED"
    assert deps.store.get(f"p/{r.artifact_id}/content.html")
    assert meta_of(deps, r.artifact_id)["status"] == "disabled"


def test_再開すると止める前の閲覧トークンがそのまま使える():
    """
    Scenario: 再開しても期限内の閲覧トークンはそのまま使える
    Given 公開を止めた共有アーティファクトと、期限内で無効にされていない閲覧トークン
    When 公開を再開する
    Then その閲覧トークンで開ける
    """
    deps, r = setup()
    before = deps.keys.get(f"token:{r.artifact_id}")
    build(deps, SuspendArtifact).run(ME, r.artifact_id)
    assert deps.keys.get(f"token:{r.artifact_id}") == "DISABLED"

    build(deps, ResumeArtifact).run(ME, r.artifact_id)

    assert deps.keys.get(f"token:{r.artifact_id}") == before
    assert meta_of(deps, r.artifact_id)["status"] == "active"


def test_止まっていないものは再開できない():
    deps, r = setup()
    with pytest.raises(ManageError) as x:
        build(deps, ResumeArtifact).run(ME, r.artifact_id)
    assert x.value.code == "NOT_SUSPENDED"


# ── プロジェクトへの出し入れ ────────────────────────────

def test_加えるとプロジェクトのトークンで開ける範囲に入る():
    deps, r, pid = with_project("PERSONAL")

    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    assert deps.keys.get(f"pp:{r.artifact_id}") == pid
    assert meta_of(deps, r.artifact_id)["projects"] == [pid]


def test_重ねて加えても二重に入らない():
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    assert meta_of(deps, r.artifact_id)["projects"] == [pid]


def test_無いプロジェクトへは加えられない():
    deps, r = setup()
    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, "nope")
    assert x.value.code == "PROJECT_NOT_FOUND"


def test_外してもアーティファクト自体は生き続ける():
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    build(deps, AssignArtifactToProject).run("unassign", ME, r.artifact_id, pid)

    assert meta_of(deps, r.artifact_id)["projects"] == []
    assert deps.keys.get(f"token:{r.artifact_id}") != "DISABLED"   # 個別には開ける
    assert deps.store.get(f"p/{r.artifact_id}/content.html")


def test_中身に書いた分類の目印では所属できない():
    """
    Scenario: 分類の目印を書き換えても見られる相手は増えない
    Given 共有アーティファクトAはどのプロジェクトにも所属していない
    When 別のプロジェクトの名前を分類の目印として書いた中身へ差し替える
    Then そのプロジェクトの閲覧トークンでは開けないままである
    """
    deps, r, pid = with_project("PERSONAL")
    tagged = HTML.replace("</head>", '<meta name="tags" content="ppp"></head>')

    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, tagged)

    meta = meta_of(deps, r.artifact_id)
    assert meta["tags"] == ["ppp"]      # 目印としては控える
    assert meta["projects"] == []       # 所属は変わらない
    with pytest.raises(KeyError):
        deps.keys.get(f"pp:{r.artifact_id}")


def test_一覧はコメントの件数を添える():
    """どれに反応が集まっているかは、次に何をするかを決める手がかりになる"""
    deps, r = setup()
    for name in ("1700000001-aaa.json", "1700000002-bbb.json"):
        deps.store.put(f"comments/{r.artifact_id}/{name}", "{}", "application/json")

    assert build(deps, ListMyArtifacts).run(ME).artifacts[0].comments == 2


def test_差し替えの区切りはコメントの件数に数えない():
    """区切りは印であって、誰かの反応ではない"""
    deps, r = setup()
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, HTML.replace("本文", "直した"))

    assert build(deps, ListMyArtifacts).run(ME).artifacts[0].comments == 0


# ── 共有と個人で出し入れの可否が変わる ──────────────────

OTHER = Caller("publisher-9")


def with_project(scope, owner=None):
    """プロジェクトが1つある状態を作る。既定では自分（ME）が作ったもの。"""
    deps, r = setup()
    deps.project_page = "<html>{{プロジェクトID}}</html>"
    p = build(deps, CreateProject).run(owner or ME, "まとめ", scope)
    return deps, r, p.project_id


def test_共有なら他の人も自分のものを入れられる():
    """持ち主が『誰でも入れてよい』と決めた前提が働く"""
    deps, r, pid = with_project("SHARED", owner=OTHER)

    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    assert deps.keys.get(f"pp:{r.artifact_id}") == pid
    assert pid in meta_of(deps, r.artifact_id)["projects"]


def test_個人のプロジェクトへは持ち主しか入れられない():
    """渡した相手に何が見えるかを、持ち主が把握し続けられるようにする"""
    deps, r, pid = with_project("PERSONAL", owner=OTHER)

    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    assert x.value.code == "PROJECT_NOT_FOUND"
    assert meta_of(deps, r.artifact_id)["projects"] == []


def test_自分のプロジェクトへは個人でも入れられる():
    deps, r, pid = with_project("PERSONAL")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    assert pid in meta_of(deps, r.artifact_id)["projects"]


def test_他人のアーティファクトは共有でも動かせない():
    """共有でも、動かせるのは自分が公開したものだけ"""
    deps, r, pid = with_project("SHARED")

    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", SOMEONE_ELSE, r.artifact_id, pid)
    assert x.value.code == "ARTIFACT_NOT_FOUND"


def test_公開が止まっているプロジェクトへは入れられない():
    deps, r, pid = with_project("SHARED")
    build(deps, ControlProjectAccess).run("suspend", ME, pid)

    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    assert x.value.code == "PROJECT_SUSPENDED"


def test_出し入れするとプロジェクトの索引と一覧が揃う():
    """所属は索引と閲覧ゲート用の投影の2か所に持つ。片方だけを書く経路を作らない"""
    deps, r, pid = with_project("SHARED")

    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)
    index = json.loads(deps.store.get(f"projects/{pid}.json"))
    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert index["memberArtifactIds"] == [r.artifact_id]
    assert [a["artifactId"] for a in listing["artifacts"]] == [r.artifact_id]

    build(deps, AssignArtifactToProject).run("unassign", ME, r.artifact_id, pid)
    index = json.loads(deps.store.get(f"projects/{pid}.json"))
    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert index["memberArtifactIds"] == []
    assert listing["artifacts"] == []
    assert deps.keys.get(f"pp:{r.artifact_id}") == ""


def test_差し替えると入っている全プロジェクトの一覧が書き直される():
    """一覧は種別と要約を含む。差し替えで変わったものが閲覧者へ届くようにする

    表示名は差し替えでは変わらない（公開したときのまま）。変わるのは
    中身から読み直す種別・要約・分類の目印である。
    """
    deps, r, pid = with_project("SHARED")
    build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    revised = HTML.replace("</head>", '<meta name="description" content="改訂した理由"></head>')
    build(deps, ReplaceArtifactContent).run(ME, r.artifact_id, revised)

    listing = json.loads(deps.store.get(f"proj/{pid}/index.json"))
    assert listing["artifacts"][0]["description"] == "改訂した理由"


def test_上限を超えてプロジェクトへ加えられない():
    """閲覧ゲートは先頭3件までしか見ない。書き手が黙って超えると、
    投稿者には成功が返り、閲覧者だけが開けない状態になる。"""
    deps, r, _ = with_project("SHARED")
    ids = []
    for i in range(MAX_PROJECTS + 1):
        p = build(deps, CreateProject).run(ME, f"まとめ{i}", "SHARED")
        ids.append(p.project_id)

    for pid in ids[:MAX_PROJECTS]:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, pid)

    with pytest.raises(ManageError) as x:
        build(deps, AssignArtifactToProject).run("assign", ME, r.artifact_id, ids[-1])
    assert x.value.code == "TOO_MANY_PROJECTS"
    assert len(meta_of(deps, r.artifact_id)["projects"]) == MAX_PROJECTS


def test_読めない記録があっても残りが並ぶ():
    """1件の不具合で一覧が空になるのを避ける。ただし黙っては落とさない——
    落とすと、投稿者が「公開したはずのものが消えた」と気づけない"""
    deps, published = setup()
    deps.store.put("meta/broken.json", "{壊れている", "application/json")

    got = build(deps, ListMyArtifacts).run(ME)

    assert [r.artifact_id for r in got.artifacts] == [published.artifact_id]
    assert got.unreadable == 1


def test_読めるものだけなら件数は0():
    deps, _published = setup()
    assert build(deps, ListMyArtifacts).run(ME).unreadable == 0

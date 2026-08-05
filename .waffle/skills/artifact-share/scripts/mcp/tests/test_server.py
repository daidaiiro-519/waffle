"""手元の受け口が、管理APIへ送る中身を正しく組み立てるかを確かめる。

実行:  python3 -m pytest scripts/mcp/tests/ -v

送信そのものは差し替えて確かめる。ここで見たいのは「どの操作をどう組み立てるか」
であって、通信ではない。通信まで含めた確認は smoke が担う。
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402


def test_持たない操作は名指しで落ちる():
    """表に無い操作は、どこへも行かずにここで落ちる。"""
    with pytest.raises(server.ToolError) as x:
        server.build_body("いない操作", {})
    assert "いない操作" in str(x.value)


def test_公開は手元のファイルを読んで中身として送る(tmp_path):
    f = tmp_path / "mock.html"
    f.write_text("<html><head><meta name=\"id\" content=\"x\"></head></html>", encoding="utf-8")

    body = server.build_body("publish", {"path": str(f)})

    assert body["action"] == "publish"
    assert body["html"] == f.read_text(encoding="utf-8")
    assert "path" not in body


def test_公開は表示名を添えられる(tmp_path):
    f = tmp_path / "mock.html"
    f.write_text("<html></html>", encoding="utf-8")

    body = server.build_body("publish", {"path": str(f), "displayName": "受付の案"})

    assert body["displayName"] == "受付の案"


def test_差し替えも同じようにファイルを読む(tmp_path):
    f = tmp_path / "new.html"
    f.write_text("<html>new</html>", encoding="utf-8")

    body = server.build_body("replace", {"artifactId": "abc", "path": str(f)})

    assert body == {"action": "replace", "artifactId": "abc", "html": "<html>new</html>"}


def test_無いファイルを指したら送らずに落ちる(tmp_path):
    with pytest.raises(server.ToolError) as x:
        server.build_body("publish", {"path": str(tmp_path / "無い.html")})
    assert "見つかりません" in str(x.value)


def test_引数を取らない操作は操作名だけを送る():
    assert server.build_body("list", {}) == {"action": "list"}


def test_渡さなかった任意の引数は送らない():
    """空文字を送ると、受け口が『空の名前を指定された』と受け取ってしまう。"""
    body = server.build_body("issue-token", {"artifactId": "abc", "name": "社内"})
    assert body == {"action": "issue-token", "artifactId": "abc", "name": "社内"}


def test_表に無い引数は送らない():
    body = server.build_body("list", {"artifactId": "abc", "余計": 1})
    assert body == {"action": "list"}


def test_必須の引数が無ければ送らずに落ちる():
    with pytest.raises(server.ToolError) as x:
        server.build_body("comments", {})
    assert "artifactId" in str(x.value)


def test_道具の一覧は表から導かれる():
    """表と一覧がずれると、呼べるのに説明が無い道具ができる。"""
    listed = {t["name"] for t in server.tool_list()}
    assert listed == set(server.TOOLS)
    for tool in server.tool_list():
        assert tool["description"]
        assert tool["inputSchema"]["type"] == "object"


def test_必須の引数が入力の形にも現れる():
    by_name = {t["name"]: t for t in server.tool_list()}
    assert by_name["comments"]["inputSchema"]["required"] == ["artifactId"]
    assert by_name["list"]["inputSchema"]["required"] == []


def test_道具の呼び出しは送信の口へ渡される(tmp_path):
    sent = {}

    def fake_call(body):
        sent.update(body)
        return {"artifactId": "aaa", "url": "https://example.com/a/aaa"}

    result = server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "list", "arguments": {}}},
        fake_call,
    )

    assert sent == {"action": "list"}
    payload = json.loads(result["result"]["content"][0]["text"])
    assert payload["artifactId"] == "aaa"


def test_組み立てに失敗したら送らずに誤りとして返す(tmp_path):
    def fake_call(body):
        raise AssertionError("送ってはいけない")

    result = server.handle(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "publish", "arguments": {"path": str(tmp_path / "無い")}}},
        fake_call,
    )

    assert result["result"]["isError"] is True


def test_知らない手続きは誤りとして返す():
    result = server.handle({"jsonrpc": "2.0", "id": 3, "method": "知らない"}, lambda b: {})
    assert result["error"]["code"] == -32601

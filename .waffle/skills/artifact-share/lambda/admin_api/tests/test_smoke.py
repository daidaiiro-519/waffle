"""上げた直後の自己点検が、壊れている環境をちゃんと落とすことを確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

点検そのものが素通りする作りだと、通ったという事実に意味が無くなる。
実際に起きた壊れ方（保管との結び付けが外れる／隔離の指定を閲覧画面まで
掛けてしまう）を作って、そのとき落ちることを見る。
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def cli():
    spec = importlib.util.spec_from_file_location(
        "artifactshare", ROOT / "scripts" / "artifactshare.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["artifactshare"] = module
    spec.loader.exec_module(module)
    return module


健全 = {
    ("GET", "https://viewer.example.net/p/zzzzzzzz/", True): (403, {}),
    ("GET", "https://viewer.example.net/p/zzzzzzzz/", False): (401, {}),
    ("GET", "https://viewer.example.net/p/zzzzzzzz/content.html", False): (
        401, {"content-security-policy": "sandbox allow-scripts; default-src 'none'"}),
    ("GET", "https://admin.example.net/", False): (200, {}),
    ("GET", "https://admin.example.net/admin/config.json", False): (200, {}),
    ("POST", "https://admin.example.net/api", False): (403, {}),
}


def 環境を作る(cli, monkeypatch, 応答):
    monkeypatch.setattr(cli, "_outputs", lambda *_a, **_k: {
        "ViewerDomain": "viewer.example.net", "AdminDomain": "admin.example.net"})

    def _probe(url, *, headers=None, method="GET"):
        鍵 = (method, url, bool(headers and "cookie" in headers))
        状態, 見出し = 応答[鍵]
        return 状態, 見出し, b""

    monkeypatch.setattr(cli, "_probe", _probe)


def test_健全な環境なら全部通る(cli, monkeypatch, capsys):
    環境を作る(cli, monkeypatch, 健全)
    assert cli.smoke("artifact-share", None) == 0
    assert "NG" not in capsys.readouterr().out


def test_保管との結び付けが外れていれば落ちる(cli, monkeypatch, capsys):
    """この壊れ方は、正しいトークンを持つ人も含めて全員が開けなくなる"""
    壊れた = {**健全, ("GET", "https://viewer.example.net/p/zzzzzzzz/", True): (503, {})}
    環境を作る(cli, monkeypatch, 壊れた)

    assert cli.smoke("artifact-share", None) == 1
    assert "保管を引けている" in [
        行 for 行 in capsys.readouterr().out.splitlines() if 行.startswith("NG")][0]


def test_隔離の指定が閲覧画面まで掛かっていれば落ちる(cli, monkeypatch, capsys):
    """閲覧画面自身が不透明な出どころになり、コメントの読み書きが止まる。
    外から叩く確認は隔離の指定を解釈しないので、見出しの有無でしか見えない"""
    壊れた = {**健全, ("GET", "https://viewer.example.net/p/zzzzzzzz/", False): (
        401, {"content-security-policy": "sandbox allow-scripts"})}
    環境を作る(cli, monkeypatch, 壊れた)

    assert cli.smoke("artifact-share", None) == 1
    assert "閲覧画面は隔離されていない" in capsys.readouterr().out


def test_持ち込まれたHTMLが隔離されていなければ落ちる(cli, monkeypatch, capsys):
    壊れた = {**健全,
              ("GET", "https://viewer.example.net/p/zzzzzzzz/content.html", False): (401, {})}
    環境を作る(cli, monkeypatch, 壊れた)

    assert cli.smoke("artifact-share", None) == 1
    assert "持ち込まれたHTMLは隔離されている" in capsys.readouterr().out


def test_証明無しで管理操作へ通れば落ちる(cli, monkeypatch, capsys):
    壊れた = {**健全, ("POST", "https://admin.example.net/api", False): (200, {})}
    環境を作る(cli, monkeypatch, 壊れた)

    assert cli.smoke("artifact-share", None) == 1
    assert "証明無しでは管理操作へ通らない" in capsys.readouterr().out


def test_見えないものを毎回言う(cli, monkeypatch, capsys):
    """外から叩く確認だけを根拠に「通しで動いた」と言わないための一文。
    実際にこの取り違えをしたとき、外から叩く確認はすべて通っていた"""
    環境を作る(cli, monkeypatch, 健全)
    cli.smoke("artifact-share", None)

    出力 = capsys.readouterr().out
    assert "ここからは見えないもの" in 出力
    assert "隔離の指定を解釈しない" in 出力

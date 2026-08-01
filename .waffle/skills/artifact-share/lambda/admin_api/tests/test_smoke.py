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


HEALTHY = {
    ("GET", "https://viewer.example.net/p/zzzzzzzz/", True): (403, {}),
    ("GET", "https://viewer.example.net/p/zzzzzzzz/", False): (401, {}),
    ("GET", "https://viewer.example.net/p/zzzzzzzz/content.html", False): (
        401, {"content-security-policy": "sandbox allow-scripts; default-src 'none'"}),
    ("GET", "https://admin.example.net/", False): (200, {}),
    ("GET", "https://admin.example.net/admin/config.json", False): (200, {}),
    ("POST", "https://admin.example.net/api", False): (403, {}),
}


def given_environment(cli, monkeypatch, responses):
    monkeypatch.setattr(cli, "_outputs", lambda *_a, **_k: {
        "ViewerDomain": "viewer.example.net", "AdminDomain": "admin.example.net"})

    def _probe(url, *, headers=None, method="GET"):
        key = (method, url, bool(headers and "cookie" in headers))
        status, headers = responses[key]
        return status, headers, b""

    monkeypatch.setattr(cli, "_probe", _probe)


def test_健全な環境なら全部通る(cli, monkeypatch, capsys):
    given_environment(cli, monkeypatch, HEALTHY)
    assert cli.smoke("artifact-share", None) == 0
    assert "NG" not in capsys.readouterr().out


def test_保管との結び付けが外れていれば落ちる(cli, monkeypatch, capsys):
    """この壊れ方は、正しいトークンを持つ人も含めて全員が開けなくなる"""
    broken = {**HEALTHY, ("GET", "https://viewer.example.net/p/zzzzzzzz/", True): (503, {})}
    given_environment(cli, monkeypatch, broken)

    assert cli.smoke("artifact-share", None) == 1
    assert "保管を引けている" in [
        line for line in capsys.readouterr().out.splitlines() if line.startswith("NG")][0]


def test_隔離の指定が閲覧画面まで掛かっていれば落ちる(cli, monkeypatch, capsys):
    """閲覧画面自身が不透明な出どころになり、コメントの読み書きが止まる。
    外から叩く確認は隔離の指定を解釈しないので、見出しの有無でしか見えない"""
    broken = {**HEALTHY, ("GET", "https://viewer.example.net/p/zzzzzzzz/", False): (
        401, {"content-security-policy": "sandbox allow-scripts"})}
    given_environment(cli, monkeypatch, broken)

    assert cli.smoke("artifact-share", None) == 1
    assert "閲覧画面は隔離されていない" in capsys.readouterr().out


def test_持ち込まれたHTMLが隔離されていなければ落ちる(cli, monkeypatch, capsys):
    broken = {**HEALTHY,
              ("GET", "https://viewer.example.net/p/zzzzzzzz/content.html", False): (401, {})}
    given_environment(cli, monkeypatch, broken)

    assert cli.smoke("artifact-share", None) == 1
    assert "持ち込まれたHTMLは隔離されている" in capsys.readouterr().out


def test_証明無しで管理操作へ通れば落ちる(cli, monkeypatch, capsys):
    broken = {**HEALTHY, ("POST", "https://admin.example.net/api", False): (200, {})}
    given_environment(cli, monkeypatch, broken)

    assert cli.smoke("artifact-share", None) == 1
    assert "証明無しでは管理操作へ通らない" in capsys.readouterr().out


def test_見えないものを毎回言う(cli, monkeypatch, capsys):
    """外から叩く確認だけを根拠に「通しで動いた」と言わないための一文。
    実際にこの取り違えをしたとき、外から叩く確認はすべて通っていた"""
    given_environment(cli, monkeypatch, HEALTHY)
    cli.smoke("artifact-share", None)

    printed = capsys.readouterr().out
    assert "ここからは見えないもの" in printed
    assert "隔離の指定を解釈しない" in printed

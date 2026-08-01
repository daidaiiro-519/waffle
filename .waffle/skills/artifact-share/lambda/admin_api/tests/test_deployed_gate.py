"""実際に配る形の閲覧ゲートを、手元の本体と同じシナリオで確かめる。

実行:  python3 -m pytest lambda/admin_api/tests/ -v

閲覧ゲートは、置けるコードの大きさに1万バイトの上限がある。手元の本体は
注釈を厚く持っているためそのままでは入らず、配るときに注釈と空行を落として
いる。つまり、これまで検証していたものと、実際に動いていたものは別の
文字列だった。

落とすのは注釈だけのはずだが、それは意図であって保証ではない。文字列の中に
現れる `//`（例: URLの `https://`）を注釈と見誤れば、そこから先が消える。
消えても構文は通りうるので、上げてみるまで気づけない。

ここでは、配る形を作って同じシナリオへ通し、上限にも収まっていることを
確かめる。
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
本体 = ROOT / "infra" / "cloudfront-function" / "viewer-token-gate.js"
シナリオ = ROOT / "infra" / "cloudfront-function" / "tests" / "viewer-token-gate.test.mjs"


def _cli():
    """手元のCLIから、配るときの加工と上限だけを借りる。

    CLIは冒頭に uv 向けの記述を持つが、読み込むだけなら影響しない。
    加工をここへ書き写さないのは、写した時点で「配る形」でなくなるため。
    """
    spec = importlib.util.spec_from_file_location(
        "artifactshare", ROOT / "scripts" / "artifactshare.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["artifactshare"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def 配る形(tmp_path_factory):
    cli = _cli()
    加工済み = cli._lean(本体.read_text(encoding="utf-8"))
    出力先 = tmp_path_factory.mktemp("gate") / "viewer-token-gate.js"
    出力先.write_text(加工済み, encoding="utf-8")
    return cli, 加工済み, 出力先


def test_配る形が上限に収まる(配る形):
    cli, 加工済み, _ = 配る形
    大きさ = len(加工済み.encode("utf-8"))
    assert 大きさ <= cli.GATE_LIMIT, f"{大きさ} バイトで、上限 {cli.GATE_LIMIT} を超えている"


def test_文字列の中の二重斜線が消えていない(配る形):
    """`https://` を注釈と見誤ると、その行の後ろが黙って消える"""
    _cli_, 加工済み, _ = 配る形
    for 行 in 本体.read_text(encoding="utf-8").splitlines():
        素 = 行.strip()
        if 素.startswith("//") or not 素:
            continue
        assert 素 in 加工済み, f"配る形から消えている: {素}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node が無い")
def test_配る形が手元の本体と同じ振る舞いをする(配る形):
    _cli_, _加工済み, 出力先 = 配る形
    結果 = subprocess.run(
        ["node", str(シナリオ)],
        env={**os.environ, "AS_GATE_SOURCE": str(出力先)},
        capture_output=True, text=True)
    assert 結果.returncode == 0, 結果.stdout + 結果.stderr
    assert "失敗 0" in 結果.stdout, 結果.stdout

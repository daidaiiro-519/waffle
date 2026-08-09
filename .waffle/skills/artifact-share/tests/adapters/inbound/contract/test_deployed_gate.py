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

from conftest import SKILL

import pytest

ROOT = SKILL
SOURCE = ROOT / "infra" / "cloudfront-function" / "viewer-token-gate.js"
SCENARIOS = ROOT / "infra" / "cloudfront-function" / "tests" / "viewer-token-gate.test.mjs"


def _cli():
    """手元のCLIから、配るときの加工と上限だけを借りる。

    CLIは冒頭に uv 向けの記述を持つが、読み込むだけなら影響しない。
    加工をここへ書き写さないのは、写した時点で「実際に配る形」でなくなるため。
    """
    spec = importlib.util.spec_from_file_location(
        "artifactshare", ROOT / "scripts" / "artifactshare.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["artifactshare"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def deployed_form(tmp_path_factory):
    cli = _cli()
    leaned = cli._lean(SOURCE.read_text(encoding="utf-8"))
    target = tmp_path_factory.mktemp("gate") / "viewer-token-gate.js"
    target.write_text(leaned, encoding="utf-8")
    return cli, leaned, target


def test_配る形が上限に収まる(deployed_form):
    cli, leaned, _ = deployed_form
    size = len(leaned.encode("utf-8"))
    assert size <= cli.GATE_LIMIT, f"{size} バイトで、上限 {cli.GATE_LIMIT} を超えている"


def test_文字列の中の二重斜線が消えていない(deployed_form):
    """`https://` を注釈と見誤ると、その行の後ろが黙って消える"""
    _cli_, leaned, _ = deployed_form
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or not stripped:
            continue
        assert stripped in leaned, f"配る形から消えている: {stripped}"


@pytest.mark.skipif(shutil.which("node") is None, reason="node が無い")
def test_配る形が手元の本体と同じ振る舞いをする(deployed_form):
    _cli_, _leaned, target = deployed_form
    result = subprocess.run(
        ["node", str(SCENARIOS)],
        env={**os.environ, "AS_GATE_SOURCE": str(target)},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "失敗 0" in result.stdout, result.stdout

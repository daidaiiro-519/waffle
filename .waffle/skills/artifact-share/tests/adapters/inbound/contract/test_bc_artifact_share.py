"""閲覧可否の判定が守ることを、業務サービスシナリオに沿って確かめる。

実行:  python3 -m pytest tests/ -v

この判定に Python の実装は無い。開けるかどうかを判じる瞬間は閲覧者の要求時で、
その瞬間に居るのは閲覧ゲートのランタイムだけなので、業務のLambdaの側には
置いていない。宣言された唯一の実装は infra/cloudfront-function/viewer-token-gate.js
であり、Python 側を探しても見つからないのは欠落ではない。

だからここで確かめるのは、配る形の閲覧ゲートを実際に走らせたとき、シナリオが
1つずつ通ることである。判定をここで書き直さない——書き直すと同じ規則の写しが
増えるだけで、突き合わせにならない。どちらが正かも決められなくなる。

シナリオと実行の対応は、向こうのラベルが仕様のシナリオ名と一字一句同じである
ことで保つ。先頭の宣言行が仕様との突き合わせのキーで、続くGiven/When/Thenは
仕様の文言をそのまま写したもの。ラベルを言い換えると、ここが落ちる。

対象の仕様: bc-artifact-share（業務サービス: 閲覧可否の判定）
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

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node が無い")


def _cli():
    """手元のCLIから、配るときの加工だけを借りる。

    加工をここへ書き写さないのは、写した時点で「実際に配る形」でなくなるため。
    """
    spec = importlib.util.spec_from_file_location(
        "artifactshare", ROOT / "scripts" / "artifactshare.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["artifactshare"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate_run(tmp_path_factory):
    """配る形の閲覧ゲートを1度だけ走らせ、その出力を配る。

    手元の本体ではなく配る形に対して走らせるのは、注釈を落とす加工が振る舞いを
    変えていないことも同時に確かめるため。
    """
    cli = _cli()
    target = tmp_path_factory.mktemp("gate") / "viewer-token-gate.js"
    target.write_text(cli._lean(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")

    result = subprocess.run(
        ["node", str(SCENARIOS)],
        env={**os.environ, "AS_GATE_SOURCE": str(target)},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def _passed(output: str, label: str) -> bool:
    """そのラベルの検証が通ったか。落ちていれば NG の行が立つ。"""
    return f"OK   {label}" in output


def _ran(output: str, label: str) -> bool:
    """そのラベルの検証が、そもそも走ったか。"""
    return f"OK   {label}" in output or f"NG   {label}" in output


def _assert_scenario(output: str, label: str) -> None:
    """仕様の名前でラベルを引き、走っていて、かつ通っていることを確かめる。

    走っていないことと落ちたことを分けるのは、ラベルを言い換えられたときに
    「検証が消えた」と読めるようにするため。落ちたのと同じ扱いにすると、
    紐づけが切れたことに気づけない。
    """
    assert _ran(output, label), f"仕様の名前で検証が見つからない（言い換えられた？）: {label}"
    assert _passed(output, label), f"検証が落ちている: {label}"


def test_個別の閲覧トークンで開く(gate_run):
    """
    Scenario: 個別の閲覧トークンで開く
    Given 共有アーティファクトAが公開されている
    When Aのアーティファクト閲覧トークンで開こうとする
    Then 開ける
    """
    _assert_scenario(gate_run, "個別の閲覧トークンで開く")


def test_プロジェクト閲覧トークンで開く(gate_run):
    """
    Scenario: プロジェクト閲覧トークンで開く
    Given 共有アーティファクトAが公開されており、プロジェクトPに所属している
    When プロジェクトPのプロジェクト閲覧トークンで開こうとする
    Then 開ける
    """
    _assert_scenario(gate_run, "プロジェクト閲覧トークンで開く")


def test_公開停止したものはプロジェクト閲覧トークンでも開けない(gate_run):
    """
    Scenario: 公開停止したものはプロジェクト閲覧トークンでも開けない
    Given 共有アーティファクトAがプロジェクトPに所属している
    And 共有アーティファクトAが公開停止されている
    When プロジェクトPのプロジェクト閲覧トークンでAを開こうとする
    Then 開けない

    交差条件。片方だけを見ると、公開を止めたはずのものがプロジェクトの
    トークンで開ける欠陥になる。この順序は閲覧ゲートにしか存在しないので、
    ここが唯一の守り手になる。
    """
    _assert_scenario(gate_run, "公開停止したものはプロジェクト閲覧トークンでも開けない")


def test_所属していないものは開けない(gate_run):
    """
    Scenario: 所属していないものは開けない
    Given 共有アーティファクトBがプロジェクトPに所属していない
    When プロジェクトPのプロジェクト閲覧トークンでBを開こうとする
    Then 開けない
    """
    _assert_scenario(gate_run, "所属していないものは開けない")


def test_無効にした閲覧トークンは使えない(gate_run):
    """
    Scenario: 無効にした閲覧トークンは使えない
    Given 共有アーティファクトAに2本のアーティファクト閲覧トークンがある
    When 一方を無効にして、その閲覧トークンで開こうとする
    Then 開けない
    And もう一方の閲覧トークンでは開ける

    Then が2つあるので、向こうでは2行に分かれる。どちらも仕様の名前を頭に
    持つので、片方だけが消えてもここで分かる。
    """
    _assert_scenario(gate_run, "無効にした閲覧トークンは使えない：開けない")
    _assert_scenario(gate_run, "無効にした閲覧トークンは使えない：もう一方の閲覧トークンでは開ける")

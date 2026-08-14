"""業務サービスのシナリオを、実装が在るランタイムの側へ束ね直す。

一般則（ブロック種別→層）が、この文脈が既に名指ししていた例外に追いついて
いなかった。個別の宣言が例外を明示しているときは、直すのは一般則の側。
"""
import json
import subprocess

PATH = ".waffle/documents/coding/test-standard-artifact-share.json"
CWD = "/home/daidaiiro/workspace/waffle"

blocks = [
    {"block": "invariantScenarios", "layer": "domain", "testType": "unit"},
    # 閲覧可否の判定は閲覧ゲートに実装が宿る。層を持たないランタイムなので、
    # placementByTarget が既に述べているとおり入口としてまとめて扱う
    {"block": "domainServiceScenarios", "layer": "inbound adapter", "testType": "contract"},
    {"block": "guaranteeScenarios", "layer": "application", "testType": "integration"},
    {"block": "acceptanceScenarios", "layer": "application", "testType": "acceptance"},
]

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", PATH,
     "--values", json.dumps({"content.scenarioBinding.blockPlacement": blocks},
                            ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:600])
print("STDERR:", r.stderr[:400])

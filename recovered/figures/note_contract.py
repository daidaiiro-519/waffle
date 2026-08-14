"""契約の行の note に、対象の範囲を書き足す。

3つのうち2つしか対象になっていないことを書かないと、次に読む人が
「書き漏らし」と「意図的な除外」を区別できない。
"""
import json
import subprocess

PATH = ".waffle/documents/coding/test-standard-artifact-share.json"
CWD = "/home/daidaiiro/workspace/waffle"


def q(block, expr):
    r = subprocess.run(
        ["uv", "run", "waffle", "query", "--operation", "query_path",
         "--path", PATH, "--blockKey", block, "--expression", expr],
        capture_output=True, text=True, cwd=CWD)
    return json.loads(r.stdout)["value"]


items = q("placementByTarget", "items")
for it in items:
    if it.get("layer") == "application" and it.get("testType") == "contract":
        it["note"] = (
            "port は層ではなく application が所有する要素なので、その契約テストも "
            "application の下に置く。同じ契約スイートを本物と偽実装の両方に対して実行する。"
            "対象は、本物を実物のサービスへ繋がずに動かせる口だけ——集約の読み書きと"
            "識別子の発行。招かれている人の名簿は、本物が利用者プールへ直接つながるため"
            "この束の対象外とし、偽物の側だけを保つ（規約が実物のサービスに依存する"
            "単体の検証を禁じている）。書き漏らしではなく、意図した除外である")

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill", "--path", PATH,
     "--values", json.dumps({"content.placementByTarget.items": items},
                            ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:300])
print("STDERR:", r.stderr[:200])

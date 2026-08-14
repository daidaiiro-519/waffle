"""段5：宣言を、実態が置ける形へ直す。移す前に済ませる。

足すのは、手元で動くプログラムを確かめるものの置き場所。
直すのは、テストファイル名の必須ルールの対象範囲。
"""
import json
import subprocess

PATH = ".waffle/documents/coding/test-standard-artifact-share.json"
CWD = "/home/daidaiiro/workspace/waffle"
BASE = ".waffle/skills/artifact-share/tests"

placement = [
    {"layer": "domain", "testType": "unit", "path": f"{BASE}/domain/unit/",
     "note": "配置はリポジトリ直下からの道で書く。検査はここをそのまま探すので、根を別に渡して補う仕組みは無い"},
    {"layer": "application", "testType": "unit", "path": f"{BASE}/application/unit/"},
    {"layer": "application", "testType": "acceptance", "path": f"{BASE}/application/acceptance/"},
    {"layer": "application", "testType": "integration", "path": f"{BASE}/application/integration/"},
    {"layer": "application", "testType": "contract", "path": f"{BASE}/application/contract/",
     "note": "port は層ではなく application が所有する要素なので、その契約テストも application の下に置く。同じ契約スイートを本物と偽実装の両方に対して実行する"},
    {"layer": "inbound adapter", "testType": "contract", "path": f"{BASE}/adapters/inbound/contract/",
     "note": "閲覧ゲートの振る舞いもここで確かめる。エッジランタイムは層を持たないため、入口としてまとめて扱う。ランタイムをまたぐデータの形の合意も、確かめている実装がどの層にあるかではなく、その合意が誰との間で結ばれているかで置き場所が決まるため、外と結ぶものはここへ置く"},
    {"layer": "outbound adapter", "testType": "integration", "path": f"{BASE}/adapters/outbound/integration/"},
    {"layer": "browser", "testType": "contract", "path": f"{BASE}/browser/contract/",
     "note": "利用者のブラウザで動く出荷物（管理画面・閲覧画面）を確かめる。ブラウザは層を持たないため、確かめるのは振る舞いではなく、出荷物どうしで二重に書かれた規則が一致していること。実行を伴わないので Python で書く"},
    # 手元で動くプログラムには置き場所の宣言が無く、確かめるものが直下へ溜まっていた。
    # 層を持たない領域にも行を与えるのは、ブラウザで先例がある
    {"layer": "cli", "testType": "unit", "path": f"{BASE}/cli/unit/",
     "note": "環境を作る手元のプログラムを確かめる。層の外にあるため、確かめるのは層の責務ではなく、自己点検の判断が壊れた環境で実際に落ちること。実行環境は差し替えて固定する。招かれた投稿者として動く受け口はまだ確かめるものが無いので、行を分けない"},
]

test_types = [
    {"testType": "unit", "tool": "pytest", "targets": ["domain", "application", "cli"]},
    {"testType": "integration", "tool": "pytest", "targets": ["outbound adapter"]},
    {"testType": "acceptance", "tool": "pytest", "targets": ["application"],
     "note": "仕様のシナリオを見て直接執筆する"},
    {"testType": "contract", "tool": "pytest", "targets": ["ports", "inbound adapter"],
     "note": "本物の実装と偽実装の両方が同じスイートを満たすことを確かめる。ランタイムをまたぐデータの形もここで確かめる"},
]

rules = [
    {"level": "禁止", "rule": "単体テストが実物のAWSサービスに依存する"},
    {"level": "推奨", "rule": "不変条件はテストダブルなしで検証する"},
    # 対象範囲を限定する。既に運用されている限定の明文化であって、新しい決まりではない
    # ——シナリオに紐づかない既存のテストは、どれも確かめている対象で命名されている
    {"level": "必須",
     "rule": "仕様のシナリオに対応するテストファイルの名前は test_{対応するspecのdocumentIdをsnake_case化したもの}.py で統一する。シナリオに紐づかないテストは、確かめている対象で命名する"},
    {"level": "必須",
     "rule": "tests/ 配下は architecture が宣言するレイヤーを第一階層とし、テスト種別を第二階層とする。ただし補助のモジュール（結線・偽物・足場）はテストではないため、この対象に含めない。取り込みの道を通す仕掛けが直下にあり、下層はそこに依存して動く"},
    {"level": "必須", "rule": "port の契約テストは、本物の実装とテスト用の偽実装の両方が同じテストスイートを満たすことを確認する"},
    {"level": "禁止", "rule": "同じ port の偽実装を複数のテストファイルに分けて定義する。少しずつ食い違い、実物なら失敗する場面で偽実装が成功してテストが緑になる"},
    {"level": "禁止",
     "rule": "同じ足場を、テストのファイルと補助のモジュールの両方に持つ。片方だけが育ち、片方だけが失敗を作れる状態になる。テストが別のテストを足場として取り込むことも同じ理由で行わない"},
    {"level": "必須", "rule": "時刻・乱数・ID生成のような非決定的な値は、テストダブルで決定的な値に固定する"},
    {"level": "禁止", "rule": "仕様の記述に、テスト層・アーキテクチャ層の内部語彙を持ち込む"},
]

values = {
    "content.placementByTarget.items": placement,
    "content.testTypes.items": test_types,
    "content.rules.items": rules,
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", PATH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:600])
print("STDERR:", r.stderr[:400])

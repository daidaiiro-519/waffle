"""宣言を先に直す：conceptPlacement を3分割し、domain-service の pattern を広げ、tree を追随させる。"""
import json
import subprocess

ARCH = ".waffle/documents/coding/architecture-artifact-share.json"
CWD = "/home/daidaiiro/workspace/waffle"

placements = [
    {"concept": "usecase", "placements": [{"path": "application/usecases"}],
     "pattern": "エントリメソッド1つ・ドメインは port 経由で呼ぶ"},
    {"concept": "aggregate", "placements": [{"path": "domain/entities"}],
     "pattern": "整合性境界を持つクラス・不変条件をメソッド内で強制"},
    {"concept": "entity", "placements": [{"path": "domain/entities"}],
     "pattern": "同一性は id・集約の内側でのみ可変"},
    {"concept": "value-object", "placements": [{"path": "domain/value_objects"}],
     "pattern": "不変（frozen dataclass）・値等価。2つの集約が同じ名前で宣言する値は、複製せず1つ置いて共有する"},
    {"concept": "domain-service", "placements": [{"path": "domain/services"}],
     "pattern": "ステートレス・集約の内側に置けない業務上の計算や判断（複数集約を跨るものを含む）"},
    {"concept": "repository",
     "placements": [{"role": "interface", "path": "application/ports"},
                    {"role": "implementation", "path": "adapters/outbound"}],
     "pattern": "aggregate の load/save・集約1つに1リポジトリ"},
    {"concept": "port", "placements": [{"path": "application/ports"}],
     "pattern": "application が要求する driven インターフェース（Protocol）。構造体のフィールドとして持たず、型として宣言する"},
    {"concept": "inbound-adapter", "placements": [{"path": "adapters/inbound"}],
     "pattern": "外部入力を usecase 呼び出しへ変換・判断を持たない"},
    {"concept": "outbound-adapter", "placements": [{"path": "adapters/outbound"}],
     "pattern": "port を実装・外部ライブラリをここに閉じ込める。合成ルートの中に無名で書かない"},
]

tree = """domain/
  entities/            整合性の境界を持つもの（集約・エンティティ）
  value_objects/       書き換えられない値。2つの集約が共有するものもここに1つ置く
  services/            集約の内側に置けない業務上の判断・計算
application/
  usecases/            1 usecase = 1 module
  ports/               application が外部へ要求するインターフェース
adapters/
  inbound/             受け口（Lambda handler・経路の振り分け）
  outbound/            S3 / KVS / Cognito への出口
shared/                結果型・エラー
main.py                結線（合成ルート・層のグラフの外）

この根の外（スキル直下）に、層を持たないと宣言した領域が並ぶ。
うち2つは利用者のブラウザで動く出荷物で、業務の判断は置かない:
  tests/                 テスト。配置は test-standard-artifact-share が宣言する
  infra/cloudfront-function/  閲覧ゲート（別ランタイム）
  infra/contract/        ランタイムをまたぐデータの形
  scripts/app/           管理画面。利用者のブラウザで動く出荷物
                       （利用者プールとのやり取りは、この画面が直接行う）
references/templates/  閲覧画面。利用者のブラウザで動く出荷物
                       （反応の書き込みは、この画面が保管へ直接行う）
scripts/               手元で動くプログラム
    artifactshare.py     環境を作るCLI。クラウドの権限で動くため、管理操作を持たない
    mcp/                 招かれた投稿者としての受け口。合言葉で本人確認を通り、クラウドの権限を使わない"""

values = {
    "content.conceptPlacement.items": placements,
    "content.layout.tree": tree,
}

r = subprocess.run(
    ["uv", "run", "waffle", "scaffold", "--operation", "fill",
     "--path", ARCH, "--values", json.dumps(values, ensure_ascii=False)],
    capture_output=True, text=True, cwd=CWD)
print(r.stdout[:1200])
print("STDERR:", r.stderr[:800])

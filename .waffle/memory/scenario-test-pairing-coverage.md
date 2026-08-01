---
name: scenario-test-pairing-coverage
description: specのシナリオ417件のうち167件が誰とも突き合わされていない実測結果と、その測り方
metadata:
  node_type: memory
  type: project
---

2026-08-01時点で、specが宣言するシナリオ417件のうち、規約（test-standard-waffleのscenarioBinding）が定める配置にテストファイルが存在するのは250件のみ。残り167件はドリフト検知の射程に入っていない。

| シナリオ種別 | 相手あり / 総数 | 配置 |
|---|---|---|
| acceptanceScenarios | 204 / 303 | tests/acceptance |
| guaranteeScenarios | 36 / 60 | tests/integration |
| invariantScenarios | 10 / 25 | tests/unit |
| domainServiceScenarios | **0 / 29** | tests/unit |

特に大きいのは次の2つ。

- `domainServiceScenarios` は全滅（bc-waffle 24件・bc-artifact-share 5件）。境界づけられたコンテキストのドメインサービスのシナリオに対応するテストが1つも無い
- artifact-share の全ユースケース（uc-invite-publisher 10件、uc-assign-to-project 9件、uc-post-comment 8件ほか計90件超）が丸ごと相手なし。テストが `tests/` の外（`.waffle/skills/artifact-share/lambda/admin_api/tests/`）にあり、実装モジュール由来の命名なので、パスからもspec名からも対応先が引けない

測り方は、各spec documentのシナリオブロックを `waffle query --operation query_path` で読み、documentIdをsnake_case化した `test_{id}.py` が規約の配置ディレクトリに存在するかを見るだけ。**この測定を行う正式なコマンドは存在せず、その場限りのスクリプトで測った。**

一覧する手段は `check-scenario-drift` へ全体走査として足すことにした（同じサイクルで実装する）。当初これを「置き場所が自明でない新規capability」と判断したが誤りで、他のドリフト検知5つ（実装クラス・操作・集約・業務サービス・schema版）は既に置き場所を受け取って全体を走査し、`missing_implementation_file` のような「宣言はあるが相手が無い」報告を持っている。1組ずつしか受け付けないのは `check-scenario-drift` だけで、例外はこちらだった。1組の呼び方も残す——書き込み起点のHookは1組、一通り作り終えたときの品質確認は全体、と使い分ける。

**Why:** 突き合わせのキーをテスト関数名から宣言行へ移す作業の中で、「Gherkinのシナリオはすべてドリフト検知できる仕様か」という問いに答えるために測った。仕様上は4種すべてが対象だが、組が存在しなければ何も起きない。この差は数字にしないと見えない。キー変更は組が成立している250件の中での突き合わせ方を変えるもので、167件には効かない。

**How to apply:** 「ドリフト検知が効いている」を根拠に品質を語るときは、その対象が全体の6割であることを前提にする。全体走査が入れば167件は報告されるようになるが、テストを書く作業そのものは別（そもそも書かれていないテストを書く話）。新しい仕組みを足したくなったときは、**まず既存の兄弟がどうしているかを全部見る**——今回は5つの前例があるのに1つだけ見て「前例が無い」と判断しかけた。再測定が必要になったら、上記の測り方をそのまま使う。

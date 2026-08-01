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

一覧する手段の新設は別サイクルで扱うと決めた。置き場所が自明でないため——`check-spec-integrity` は守備範囲がspecツリー内部（テストファイルは範囲外）、`check-scenario-drift` はspecとテストファイルを1組ずつ渡す前提で、どちらにも素直に収まらない。

**Why:** 突き合わせのキーをテスト関数名から宣言行へ移す作業の中で、「Gherkinのシナリオはすべてドリフト検知できる仕様か」という問いに答えるために測った。仕様上は4種すべてが対象だが、組が存在しなければ何も起きない。この差は数字にしないと見えない。キー変更は組が成立している250件の中での突き合わせ方を変えるもので、167件には効かない。

**How to apply:** 「ドリフト検知が効いている」を根拠に品質を語るときは、その対象が全体の6割であることを前提にする。167件を減らす作業は、キー変更とは別の作業（そもそも書かれていないテストを書く）として扱う。一覧手段を作るサイクルを起こすときは、置き場所の判断から始める（既存2コマンドのどちらかへ足すのか、第三のものにするのか）。再測定が必要になったら、上記の測り方をそのまま使う。

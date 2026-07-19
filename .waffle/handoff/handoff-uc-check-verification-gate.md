## 概要

実装完了から検証フェーズへ進んでよいかを機械的に判定するusecaseの設計判断を実装へ引き継ぐ。

---

# 実装完了→検証フェーズへ進んでよいかを機械的に判定する実装引き継ぎ：handoff-uc-check-verification-gate

## 引き継ぎ元spec

uc-check-verification-gate

---

## 完成イメージ

---

## 使われ方（実際の呼び出し例）

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | sd-flow-gateをsd-reconciliationから分離するのは妥当（関心事の性質が異なる） | sd-reconciliationは既存成果物間の構造的整合性（spec同士・spec⇄テストシナリオ名・Document⇄Schema版等）を検知するのに対し、sd-flow-gateはプロセスの現在状態（テスト結果・検出力指標）から次フェーズへの遷移可否を判定するもので、扱うデータも問いの性質も異なる。同じ「check」という語を使うが本質的に別の関心事であり、分離が支持される。 |
| ddd-advisor / tech-lead-advisor | sd-flow-gateの「中核」分類は、当初tech-lead-advisorから「一般（既製ツールで解決済みの領域では）」という異論が出たが、ユーザーが「Waffle固有の開発フロー（spec-first+TDDプロセス）の判定である」と明言したことで中核判定を確定した | 「テスト緑＋mutation score閾値で完了判定」だけならSonarQube等の既製Quality Gateと変わらないが、実際の判定はspecのacceptanceScenarios（Waffle独自のドキュメントモデル）とテストの対応関係を前提にしており、既製ツールが理解できないWaffle固有の構造を扱う。この点が中核判定の最終的な根拠。 |
| tech-lead-advisor | usecase自身がpytest/mutmut等のテストを実行してはならない | 既存check-*系usecase（例: check_scenario_drift）は「実行/意味理解はしない（AST解析のみ）」という設計規律を持つ。テスト実行結果は既に生成済みの構造化データとして受け取り、実行そのものはinfra層（呼び出し側/アダプタ）の責務とする。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | 既存check_scenario_driftを内部で呼び出して再利用する | missing_in_tests/orphaned_in_tests/gherkin_mismatches/matchedという出力は、既存のCheckScenarioDrift usecaseがそのまま持っている。uc-check-verification-gateの実装は、このusecaseをコンポジション（内部呼び出し）で再利用し、判定ロジック（優先順位: missing_in_tests > orphaned/mismatch > failed > ready）だけを追加する。ゼロから照合ロジックを再実装しない。 |

---

## 既知の制約・トレードオフ

- testResultsPathの形式は、pytestのnodeidやJUnit XML等の特定テストランナー・言語のネイティブ出力ではなく、check_scenario_driftが使うのと同じシナリオ名の語彙でpassed/failedを表す抽象形式（{passed: [...], failed: [...]}）。ネイティブ出力からこの抽象形式への変換（正規化）はusecaseのスコープ外＝呼び出し側/アダプタの責務。この境界線は、sd-reconciliation配下の既存check-*系usecaseが特定言語・ツールに一切依存しない設計を貫いていることと整合させるために、意図的に引いた。
- 複数の条件に同時に該当する場合の優先順位は missing_in_tests > orphaned_in_tests/gherkin_mismatches > failed > ready の順で固定。実装時にこの順序を変更しない。
- mutation score等の検出力指標は今回のスコープ外（brainstormの合意通り、最初の1フェーズ分＝テスト緑＋spec対応関係のみを実装する。検出力指標は2件目のフェーズが必要になった時点で改めて検討する）。

# ブレインストーミング: qa-advisorの設計

**目的:** advisorエコシステムに新設する`qa-advisor`（シナリオ・テストの品質評価担当）が
何を持つべきか、既存advisor（tech-lead-advisor）との境界を明確にした上で、守備範囲と
原典知識の方針を決める。
**モード:** 問題解決→アイデア発散
**作成日:** 2026-07-11

---

## 経緯: `#1 シナリオ検死官`（mutation testingでシナリオの弱さを機械採点）の再検討から

`has-udd/docs/brainstorm/brainstorm-waffle-next-evolution.md`論点1で提案されていた
「シナリオ検死官」は、当初は新規usecase（reconcileの一種）として構想されていた。しかし
検討の結果、これは**usecaseではなくadvisorのカテゴリーに属する**と判断した。

**理由:** Waffleは「構造は機械的に決定的コードで判定する（usecase/reconcile）」
「意味は人間の判断が要るためテキストベースの疎結合インターフェースを通してAIエージェント
（advisor）に委ねる」という2トラック設計を最初から持っている（`sd-reconciliation`の
`implementationGuidance`参照）。シナリオ・実装の「意味的な健全性」（弱いテストか・実際に
バグを検出できるか）は後者の性質であり、機械的な決定論だけでは判定しきれない。

---

## 既存advisorとの境界確認

### tech-lead-advisorとの境界（本ブレストで確定）

当初「tech-lead-advisorはレイヤー配置・依存方向のみを扱う」という理解で議論していたが、
実際の定義（`role`/`knowledgeRefs`）を確認したところ、以下まで既に含んでいた:

- `architecture-tech-stack-selection-chain`（技術スタック選定）
- `architecture-layer-naming-convention`（レイヤーごとの命名・コーディング規約）
- `architecture-test-strategy-by-layer`（**レイヤーに基づくテスト戦略**）

実務のテックリードの職責（アーキテクチャ〜設計〜実装〜技術選定〜規約〜テスト戦略）と
ほぼ一致する範囲を最初から持っており、「レイヤー配置・依存方向のみ」という要約は不正確
だった（purposeの一文だけを見て説明を狭めてしまっていた）。

**それでも重複しない、と判断した根拠:** `architecture-test-strategy-by-layer`の中身は
「**どの層にどのテスト種別（単体/結合/E2E）を書くべきか**」という**配置**の判断であり、
「**このシナリオ・テストが実際にリスクに見合う強さを持っているか**」という**品質評価**
とは別軸。

**確定した役割分担（tech-lead-advisor・ddd-advisorへの実相談を経て確定・3分割）:**

tech-lead-advisorに実際に相談したところ、`architecture-test-strategy-by-layer.md`自身が
「テストの比率・厚み（テストピラミッドの形）はddd-advisorの`design-heuristics.md`が扱う」と
明記しており、当初の2分割（tech-lead-advisor/qa-advisor）では見落としがあった。ddd-advisor
にも相談し、以下の3分割で確定した:

| 担当 | 判断内容 |
|---|---|
| ddd-advisor（`design-heuristics`） | テストの**比率**（ピラミッド/ダイヤモンド/逆ピラミッド）をサブドメイン分類・実装方法から決める |
| tech-lead-advisor（`test-strategy-by-layer`） | 個々のテストを**どのレイヤー境界**に置くか決める |
| qa-advisor（新設） | テストが**振る舞い単位で構造化されているか**（実装ファイルと1:1に肥大化していないか）・**個々のテストの強度**（カバレッジ通過だけが目的の空疎なテストでないか）を評価する |

**diagnostic feedback loopの必要性（ddd-advisorからの指摘）:** qa-advisorが「弱いテスト」を
発見した際、その原因が(a)単なる執筆品質の問題（qa-advisor自身の守備範囲）なのか、
(b)上流の設計判断ミス（サブドメイン分類と実装方法の不一致、＝ddd-advisorの守備範囲）に
起因するものかを区別できないと誤診断のリスクがある。qa-advisorの判断フローには、
「弱いテストを見つけたら、まず上流（ddd-advisor/tech-lead-advisor）の判断が正しく
適用されているかを確認する」という差し戻し経路を持たせる。

### QAの職責範囲（本ブレストで確定）

現代のアジャイル/DevOps以降の実務（shift-left・SDET的実践）に基づく整理:

- **テストの執筆はエンジニア自身の仕事**（TDD）。QAが全てのテストを書くわけではない
- **QAはテストの"評価者"であって"作者"ではない**——既存advisorの動作モデル（助言を返すが
  直接コード・specを書き換えない）とも一致する
- QAが担うのは: リスクベースのテスト戦略・探索的テスト・Definition of Doneの定義・
  **品質ゲートの番人**
- 評価で不足が見つかった場合、実際に直すのは呼び出し元（specを書いたAI/エンジニア自身）
  ——既存advisor全員と同じ「評価はするが手は動かさない」という役割分担

### 実例で裏付けられたqa-advisorの具体的な守備範囲（ユーザーの実体験より）

AIにテストを大量生成させると、以下の症状が実際に頻発する:

- **カバレッジを通すためだけの空疎なテスト**——カバレッジ自体は業務ロジックで必須だが、
  「通すのに苦労する実装」自体がテスト容易性（testability）の設計問題（tech-lead-advisor領域）
  である場合が多く、テストを取り繕う前にそちらを疑うべき
- **実装ファイルと1:1のテストが肥大化していく**——カバレッジ駆動でテストを書くと、実装ファイルを
  分割しすぎた分だけテストも増殖する。テストが「正しい境界（振る舞い単位）」ではなく
  「実装の詳細」に密結合していると、ソースコードを触るたびに関連テストの修正が連鎖する悪循環を生む

これは確立されたテスト理論の用語がある:

- **テストの臭い（test smells）**、特に「実装をなぞるテスト」「カバレッジ駆動テスト」
- **振る舞いのテスト vs 実装のテスト**（sociable/solitary unit testsの区別、Martin Fowlerの整理）
- **test-induced design damage**（DHHが"TDD is dead"論争で指摘した、実装への過度な結合によって
  リファクタが困難になる現象）

qa-advisorの原典知識候補にこれらを追加する。

---

## 未決着: qa-advisorの原典知識（バックボーン）をどう構成するか

`ux-advisor`設計時と同様、単一の権威ある書籍ではなく複数の確立された公開知見の総合に
なる可能性が高い。実例で裏付けが取れた候補（優先度高）と、まだ裏付けの無い候補
（優先度中・未検討）を分けて記録する。

**裏付けが取れた候補（本ブレストの実例より）:**
- テストの臭い（test smells）——特に「実装をなぞるテスト」「カバレッジ駆動テスト」
- 振る舞いのテスト vs 実装のテスト（sociable/solitary unit testsの区別、Martin Fowler）
- test-induced design damage（実装への過度な結合によるリファクタ困難化）
- Mutation testingの考え方（`#1シナリオ検死官`の技術的中核。個々のテストの強度評価）

**web調査済み・KnowledgeSchema文書として作成済み（2026-07-11）:**
deep-researchワークフロー（5テーマ・107エージェント・adversarial検証付き）で調査し、
うち4テーマは高信頼度の裏付けが取れたため、`.waffle/documents/knowledge/`配下に
KnowledgeSchema文書として作成・validate・render済み:

- `tdd.json`（Kent Beck『Test-Driven Development: By Example』。Red/Green/Refactor）
- `boundary-value-analysis-equivalence-partitioning.json`（Glenford Myers起源、
  ISTQB Foundation Level Syllabusで標準化）
- `risk-based-testing.json`（Felderer & Schieferdecker 2014、ISTQB glossary）
- `exploratory-testing.json`（James Bach / Cem Kaner、
  『Lessons Learned in Software Testing』2001年）

**web調査済み・KnowledgeSchema文書として作成済み（2026-07-11、追加分）:**
本ブレスト前半で見つけた4候補（test smells/sociable-solitary unit tests/
test-induced design damage/mutation testing）についても、deep-researchワークフロー
（6角度・104エージェント・adversarial検証付き）で追加調査し、`.waffle/documents/knowledge/`
配下にKnowledgeSchema文書として作成・validate・render済み:

- `test-smells.json`（Gerard Meszaros『xUnit Test Patterns: Refactoring Test Code』
  2007年。Code/Behavior/Project Smellsの3分類、Code Smellsの代表例5種）
- `sociable-solitary-unit-tests.json`（Jay Fields考案・Martin Fowlerがbliki記事
  「UnitTest」2014年で整理・普及）
- `test-induced-design-damage.json`（DHH 2014年の一連のブログ記事とMartin Fowler
  司会『Is TDD Dead?』対談シリーズ。DHH側/Beck・Fowler側の対立を中立的に整理）
- `mutation-testing.json`（現代ツール文書によるmutant/killed/survivedの基本定義。
  起源論文Hamlet 1977・DeMillo et al. 1978は書誌情報のみ確認でき、論文本文への
  直接検証は今回未達——provenance.caveatsに正直に記録）

これで`定義済みDefinition of Done`と合わせ、qa-advisorの原典知識候補は当初の
動機（`#1シナリオ検死官`）に直結する9本が出揃った。

**未完了・追加調査が必要:**
- ~~Definition of Done（DoD）~~ → 完了（2026-07-11、`definition-of-done.json`）
- ~~test smells/sociable-solitary/test-induced design damage/mutation testing~~
  → 完了（2026-07-11、上記4本）

### 副産物: KnowledgeSchema自体の構造レビュー（v1→v2、2026-07-11）

4文書を作成する過程で、ユーザーから`KnowledgeSchema`自体の構造指摘を受け、v2へ移行した:

1. **`principles.text`（1文字列）→`principles.items`（配列）**: 複数の独立した主張
   （定義・成立根拠・優先順位・副次的効果等）が1つの長文に混在していた問題を解消
2. **`provenance.text`→`provenance.source`/`caveats`**: 「出典」と「まだ確証が
   得られていない留保事項」という別の関心事が混在していた問題を解消
3. **`classifications`/`decisionCriteria`/`antiPatterns`/`relatedConcepts`に
   `emptyReason`フィールドを追加**: itemsが空のとき、ブロックが「存在するが中身が空」の
   状態を放置せず、必ず理由を明記するよう強制。実際にこの移行作業中、`risk-based-testing`
   （分類0件・判断基準0件・実例が空文字）等、本来書くべき内容が抜けていた箇所を複数発見し
   補完した
4. `classifications`/`decisionCriteria`/`examples`/`antiPatterns`/`provenance`/
   `relatedConcepts`を`KnowledgeContent`の必須プロパティに昇格（`scaffold create`が
   既に必ず全ブロックの空スケルトンを生成する実態に、schemaの`required`宣言を合わせた）

既存42文書＋新規4文書、計46文書全てをv2へ移行し、pytest 194件green・
check-schema-version-drift clean・render確認済み。

---

## 次のアクション

1. ~~tech-lead-advisorとの境界を確定する~~ → 完了（本ブレストで確定・ddd-advisorも含めた3分割に修正）
2. qa-advisorの原典知識（バックボーン）のアイデアダンプを行う（`ux-advisor`設計時と
   同じ手順: 既存advisorへの事前相談→アイデアダンプ→論点整理→合意）
   → 4テーマ完了・KnowledgeSchema文書化済み（tdd/boundary-value-analysis-
   equivalence-partitioning/risk-based-testing/exploratory-testing）
3. ~~Definition of Done（DoD）を別途追加調査する~~ → 完了（2026-07-11、
   `definition-of-done.json`として文書化。deep-research最終統合ステップが
   バグりダミー値を返したため、journal.jsonlの生検証結果から手動で再構成した）
4. ~~test smells/sociable-solitary/test-induced design damage/mutation testingの
   一次資料裏付けを行う~~ → 完了（2026-07-11、4本文書化。詳細は上記）
5. qa-advisor Skill本体の新設に着手（2026-07-11〜）。9本のKnowledge文書が
   出揃ったため、knowledgeRefsとして束ね、purpose/role/判断基準・回答テンプレートを
   ddd-advisor/tech-lead-advisorと同型で構築する

---

## qa-advisorをどう運用に組み込むか（2026-07-11）

### 「#4ゼロコード審判」の運用ループを検討する過程で判明した、4層の役割分担

`#4`（未踏行の検知）を実際に運用する場合、「未踏行を見つけたらどうするか」を
検討したところ、qa-advisor単体では完結しないことが判明した。qa-advisorを含む
全advisorは一貫して「抽象化された状況を渡されて、助言を文章で返すだけ」という
動作モデルであり、直接ソースコードを読みに行ったり、ファイルを編集したりはしない。
「未踏行の実コードを読んで、正当な例外か・削除すべきか・specへ遡及追記すべきかを
判断し、実際に行動する」という一連の作業は、能動的に読み・判断し・手を動かす
**Agent**の守備範囲であり、Skillの守備範囲ではない。

4層に分けて整理した:

| 層 | 何を持つか | どこに置くか |
|---|---|---|
| 検知 | 未踏行を機械的に列挙する | usecase（reconcile） |
| 判断基準 | 「正当な例外／delete／spec遡及追記」の決定木 | qa-advisorのKnowledge文書（新設予定） |
| 実行 | 実コードを読み、判断を仰ぎ、行動する | Agent（Orchestrator、または委譲されたSubagent） |
| 連携の配線 | 「検知結果が出た後、qa-advisorに相談してから行動する」という手順 | AgentSchemaの`SkillFollowUp`（`waffle.json`に既存の同型パターンあり） |

現状waffleには専用の「コーディング担当Subagent」が存在しない（`check-agent-skill-drift`
の実行結果が示す通りsubagentは0件）ため、実行主体は現時点ではOrchestrator自身になる。
これは`brainstorm-has-udd-role-agent-rethink.md`（has-uddのrole agentをPO/SM軸で
再定義する話）で保留にした「実際にコードを書く役割を専任のSubagentとして切り出すか」
という積み残しの論点に直結する。

### 常設Subagentを用意すべきか、毎回スポットで生成すべきか

ユーザーからの問い: AgentSchemaは既にOrchestrator/Subagentのスキーマを持ち、
waffleのscaffold+fill+renderの仕組みを使えば、目的・タスク・成果物イメージを
x-prompt-write通りに埋めるだけでSubagent定義（またはAgent呼び出しパラメータ）を
その都度生成できる。この場合、常設のSubagentを用意するメリットは薄いのではないか。

**訂正（2026-07-11、ユーザー指摘により確定）:** AIは当初これをYAGNI
（`architecture-evidence-based-scope`、同じ組み合わせの実例が複数回観測
されてから永続化を判断する）で処理しようとしたが、ユーザーから明確な訂正が
入った。この判断は「実現の頻度」で決める話ではなく、**Waffleを個人利用ではなく
OSSとして出荷する以上、プロダクトの仕組みとして今すぐ確定させるべき
コンセプトレベルの決定**である。理由は2点:

1. 委譲するタスクごとに目的・受け入れ基準が変わるため、「同じ組み合わせの
   繰り返し」という発生パターン自体を前提にできない
2. Claude Code・GitHub Copilot・Kiro等、ツールごとにエージェント定義ファイルの
   形式が異なり共通化できない——ツール固有形式で永続登録する設計は、そもそも
   OSSとして複数ツールにまたがる想定と相性が悪い

**確定した設計:** Subagentは**都度、Orchestratorが動的にゴール指定書を
render+deployせずテキストとして組み立てる**方式に統一する（`.claude/agents/`への
永続登録はしない）。これは`AgentSchema/v2`として実装済み——`SubagentContent`を
goal/persona/skillPreloads/task/deliverable/acceptanceCriteriaの物語順で再構成し、
`x-render-target.deploy.subagent`を空にして永続ファイルを書き出さないようにした
（実際にddd-advisorへの並列dispatchで動作検証済み。詳細はコミット`238a13c`）。

**次のアクション:** qa-advisor Skill本体を新設した後、実際の批評依頼で
`AgentSchema/v2`のgoal-dispatch機構を使って呼び出す運用を試す。

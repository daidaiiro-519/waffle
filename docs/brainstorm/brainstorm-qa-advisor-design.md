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

**まだ裏付けの無い候補（次回以降のアイデアダンプで実例と照らして深掘りする）:**
- 境界値分析・同値分割等の古典的テスト設計技法
- リスクベーステスト（risk-based testing）
- Definition of Doneの構成要素
- 探索的テスト（exploratory testing）

---

## 次のアクション

1. ~~tech-lead-advisorとの境界を確定する~~ → 完了（本ブレストで確定・ddd-advisorも含めた3分割に修正）
2. qa-advisorの原典知識（バックボーン）のアイデアダンプを行う（`ux-advisor`設計時と
   同じ手順: 既存advisorへの事前相談→アイデアダンプ→論点整理→合意）
   → 一部完了（test smells/sociable-solitary/test-induced design damage/mutation testingは
   実例で裏付け済み）。残りの候補（境界値分析・risk-based testing・DoD・探索的テスト）は
   実例との照合が未了
3. 実装（実際にskill documentを新設するか）は保留。まず設計（knowledgeRefsの中身・
   判断基準の型）を固めることを優先する

# ブレスト: 進行中の検討・意思決定を記録するdocumentジャンルがWaffleに無い問題

**作成日:** 2026-07-12
**経緯:** `docs/handoff-goal-loop-orchestration.md`のような、進行中の検討・未確定の
意思決定を引き継ぐための資料を、既存のWaffle schemaに移行できるか試した。
`KnowledgeSchema/v2`への`scaffold create`を試したところ、`content.provenance.source`
（著者名・書籍/論文名・年等の出典）や`content.decisionCriteria`（確立した概念の
判断基準の分岐点）が必須になっており、いずれも「確立済みの原則」を記録する形を
前提にしていて、「まだ確定していない・進行中の検討」というジャンルには構造的に
合わないことが分かった。

---

## 発見: KnowledgeSchemaは「確立された知識」専用で、「進行中の検討」を書く場所がない

Waffleが現在持つdocumentType（AgentSchema/CodingSchema/DomainSpecSchema/
KnowledgeSchema/PresentationSpecSchema/SkillSchema/TemplateSchema）はいずれも、
完成した・確定した成果物を記述する前提の構造を持つ。「背景→ここまでの決定→
未決着事項→次のアクション」という、状態が変わり続ける引き継ぎメモ特有の構造
（KnowledgeSchemaでいう`provenance`/`decisionCriteria`に相当するものが無い代わりに、
「まだ結論が出ていない」ことをそのまま記録する場所が要る）を持つ既存schemaが無い。

これは`docs/handoff-*.md`のような資料が今後も増えることを踏まえると、
新しいdocumentジャンル（仮称: Handoff）を用意する余地がある、という仮説に留まる。

---

## 一度Schema実装まで進めて差し戻した経緯

このブレストを書く前に、実際に`HandoffSchema/v1`（title/background/decisions/
openQuestions/nextActions/referencesの6ブロック構成）を実装し、`docs/handoff-
goal-loop-orchestration.md`を実際に移行するところまで一度実行した。しかし、
**UDD原則（spec-first）に反してspec（.waffle/specs配下の合意）を経ずに
いきなりschema実装に進んでしまった**ため、Schema実装・関連テスト・移行済み
documentは全て撤去し、このブレストレベルまで差し戻した。

したがって次にこのアイデアを進める場合は、spec-first（`sd-schema-management`
配下でのusecase spec合意）を経てから実装すべきで、ブレストの時点でschema構造
（ブロック名・フィールド名等）を先取りして確定させないこと。

---

## 追記: Handoffは単一の形ではなく複数kindを持つのではないか（2026-07-12）

「ハンドオフって言ってもCodingにおけるハンドオフなのか、たぶんいくつかKindは
ありそうな気がする」という指摘があり、実在する3件の`docs/handoff-*.md`を
見比べたところ、確かに性質が異なることが分かった。

| ファイル | 性質 |
|---|---|
| `handoff-goal-loop-orchestration.md` | 実装方針・技術調査結果込みの引き継ぎ。CLIの実力マトリクスやPoC状況など、実装に踏み込む前の技術検討記録に近い |
| `handoff-has-udd-brainstorms.md` | 別リポジトリ（has-udd）で行われたブレストの**合意済み結論だけを要約**して移した引き継ぎ。原本は別リポジトリにあり、こちらは要約版という位置づけ |
| `handoff-has-udd-concept-map-redesign.md` | プロダクトの設計方針そのものの引き継ぎ。`★2026-07-11更新`のような追記が入り、生きた文書として更新され続けている |

この3件は「背景→決定事項→未決着事項→次のアクション」という大枠の型は
共通していそうに見えるが、それぞれ性質が異なる:
- 1件目は**技術調査寄り**（Coding領域に近い、CodingSchemaの`codingKind`
  ＝tech-stack/architecture/coding-standard/test-standardのような discriminator
  で分類される類のものかもしれない）
- 2件目は**要約・転記型**（原本が別にあり、結論だけを抽出している）
- 3件目は**生きた方針文書**（更新履歴を持つ、完全に確定してもいない）

CodingSchemaが`codingKind`という discriminator で1つのschemaの中に複数の
中身を収める設計をしている前例があるため、Handoffも同様に`handoffKind`
のようなdiscriminatorを持つ可能性がある。ただしこれもまだ**仮説**であり、
kindの種類・命名（技術調査系／要約転記系／方針文書系、というような分け方が
妥当かどうかも含め）は未検討。

---

## 追記: 「そもそも要るか」を問い直し、目的が根本的に変わった（2026-07-13）

「ハンドオフスキーマって実際のところいると思う？」という問いから議論をやり直した結果、
2026-07-12時点の仮説（技術調査系／要約転記系／方針文書系という3 kind説）は**採用しない**
ことになった。代わりに、全く別の切り口の目的に収束した。

### 検討の経緯（結論だけでなく、棄却した案も残す）

1. **「進行中の検討・未確定の意思決定を記録するジャンル」という当初の目的そのものへの疑義**
   `docs/handoff-*.md`のような資料は、実際にはコミットメッセージとブレストドキュメントで
   代替できているのではないか、という懐疑から出発した。
2. **ADR（Architecture Decision Record）ではないか、という案**
   ユーザーから「spec終わった後にcodingする時の設計実装ガイドが書かれた指示書」という
   イメージが示され、これはADRに近いのでは、と考えた。
3. **「1ドキュメント＝論点の配列」という統合案 → 棄却**
   実際の`docs/handoff-goal-loop-orchestration.md`を確認すると、論点ごとに
   「状況→確定した内容→根拠→参照」というADR的な構造を持つ節が並んでいることが分かり、
   「WIPログとADRは中身の形は同じで、決着済みか否かが違うだけではないか」という統合案を
   一度提示した。しかしユーザーから「specのADRとしては微妙」という指摘があり、
   **ADRは1決定＝1ドキュメント（不変・supersededByで覆す・specから個別に参照できる）が
   本質であり、論点を配列に束ねると個別参照も不変性も失われる**ため、この統合案は
   採用しないことになった。
4. **真のイメージ: spec→実装の橋渡しとしてのadvisor観点の永続化 → 採用**
   ユーザーの最終的なイメージは、ADRでもWIPログでもなく、
   **「抽象化されたspec（業務語彙のみ）を実装フェーズに引き継ぐ際に、advisorとの相談で
   得られた設計・実装観点を構造化保存する」**というものだった。

### 採用する目的（現時点の理解）

CLAUDE.mdに既に定義されている「Skillフォローアップ」ワークフロー
（advisorへAgentSchemaのgoal-dispatch構造で並列相談し、`template-skill-critique.md`
形式で統合する手順）を、**「specを実装に引き継ぐ」場面に適用したときの結果を
永続化する場所**、というのが現時点の合意。

- 全advisor（ddd-advisor/tech-lead-advisor/ux-advisor/qa-advisor/platform-advisor等）
  に一度声をかけ、その中で関係するadvisorが実際に観点を書き込む
  （今のSkillフォローアップは相談結果をユーザーへの回答として返すだけで、
  どこにも構造化保存されない。これが今回の出発点だった「そもそも要るか」への
  肯定的な根拠になった）
- specRef（どのusecase/aggregateから引き継ぐか）を持つ
- 各観点に「どのadvisor由来か」をタグ付けする
  （後で「なぜこう考えたか分からなくなったとき、どのadvisorに再相談すればいいか」を
  追跡できるようにするため）
- 想定される中身（未確定・粒度は要検証）:
  - `specRef`
  - 設計観点（items）: 観点名・考慮事項・関連する既存パターン・由来advisor
  - 実装観点（items）: 観点名・考慮事項（テスト戦略・レイヤー配置等）・由来advisor
  - （任意）既知の制約・トレードオフ

2026-07-12時点の「技術調査系／要約転記系／方針文書系」という3 kind仮説と、
本追記の「WIPログ統合案」は、いずれも**この目的の下では的外れだった**ため、
再開時はこの2026-07-13追記を出発点にすること。

---

## 未検討

- Handoffという名前・所属subdomain（`sd-schema-management`直下か、別途新設か）
- 既存4 documentType（Agent/Coding/DomainSpec/Knowledge/Presentation/Skill/
  Template）との住み分け方針（新schemaを増やす方針自体の是非を含む）
- 全advisor起動のタイミング・トリガー（specのstatusがVALIDATEDになった時点で
  自動的に走らせるのか、明示的にOrchestratorが判断して起動するのか）
- 「関係するadvisor」の判定方法（機械的に判定するのか、Orchestratorの裁量か）
- 1specにつき1 Handoffドキュメントなのか、複数バージョン（実装が進むにつれて
  観点が更新される）を持ちうるのか、その場合のlifecycle設計
- 設計観点・実装観点のitem粒度（1観点1item、advisorごとにブロックを分けるか
  同一配列でタグ分けするか等）は未検証

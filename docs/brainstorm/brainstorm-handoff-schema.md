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

## 未検討

- Handoffという名前・所属subdomain（`sd-schema-management`直下か、別途新設か）
- 既存4 documentType（Agent/Coding/DomainSpec/Knowledge/Presentation/Skill/
  Template）との住み分け方針（新schemaを増やす方針自体の是非を含む）
- 「進行中の検討」は本質的に短命（決着すれば別のジャンルに昇格 or 破棄される）
  という性質を、statusのenumだけで表現しきれるか

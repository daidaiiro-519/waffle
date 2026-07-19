---
name: "knowledge-cultivator"
description: "advisorのバックボーンknowledgeに追加すべき候補を検知・記録し、蓄積した候補について採用可否を人間との対話を通じて判定する際に使う。ユーザーがadvisorの判断を訂正したとき、既存knowledgeでカバーされない実例に遭遇したとき、または並列dispatchしたadvisor同士の見解が矛盾したときに使う。"
---

# advisorのknowledge候補の検知・採用判定を行うSkill：knowledge-cultivator

## 目的

advisorのバックボーンknowledgeに追加すべき候補を検知・記録し、蓄積した候補について採用可否を人間との対話を通じて判定する際に使う。ユーザーがadvisorの判断を訂正したとき、既存knowledgeでカバーされない実例に遭遇したとき、または並列dispatchしたadvisor同士の見解が矛盾したときに使う。

---

## 役割

- advisorのバックボーンknowledgeへの追加候補を、KnowledgeSchemaのDRAFT状態のdocumentとして記録する
- 蓄積されたDRAFT候補を、審査に使える形へ要約・整理する
- 候補ごとに、人間との対話（AI初期見解→ユーザー見解→AI再考見解→合意決定）を通じて採用可否を判定する

---

## 処理対象と成果物

### 処理対象

advisorのバックボーンknowledgeへの追加候補となりうる状況（ユーザーの訂正・未カバーの実例・advisor間の矛盾）、および既に記録済みのDRAFT状態のKnowledgeSchema document群。

### 成果物

DRAFT状態のKnowledgeSchema document（記録局面）、候補審査ドキュメント（棚卸し・審査局面、採用/却下/修正して採用の決定を含む）。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| knowledge候補の記録トリガーとなった状況（ユーザーによるadvisor判断への訂正／既存knowledgeでカバーされない実例／並列dispatchしたadvisor間の見解矛盾のいずれか） | 明示されなければ直前の会話からこの3種のいずれに該当するか判定する。個人の伝え方・コミュニケーションスタイルへのフィードバックはこの3種に該当せず対象外として扱う。 |
| 棚卸し対象とするDRAFT状態のKnowledgeSchema document群 | 明示されなければ既存のDRAFT状態のKnowledgeSchema documentをqueryで全て洗い出す。 |

---

## 実行手順

### Step 1: knowledge候補を記録する

3種のトリガー（ユーザーによるadvisor判断への訂正／既存knowledgeでカバーされない実例／並列dispatchしたadvisor間の見解矛盾）のいずれかを検知したら、対象advisorへのskillRefを持つKnowledgeSchema documentをstatus DRAFTで作成する。

#### ユーザーによるadvisor判断への明示的な訂正を検知する

advisorが出した結論・判断根拠に対し、ユーザーが誤りを指摘した発言をトリガーとする。

- 個人の伝え方・コミュニケーションスタイルへの指摘は対象外とする

#### 既存knowledgeでカバーされない実例に遭遇したことを検知する

advisorが判断根拠を示せない、またはバックボーン範囲外と回答した実際の状況をトリガーとする。

#### 並列dispatchしたadvisor同士の見解の矛盾を検知する

同一の相談に対して複数advisorを並列dispatchした結果、判断が食い違った場合をトリガーとする。

### Step 2: 蓄積したDRAFT候補を審査用にとりまとめる

既存のDRAFT状態のKnowledgeSchema documentをqueryで洗い出し、各候補の出典・トリガー種別を含む審査対象一覧へ要約する。採用の可否はここでは判断しない。

### Step 3: 候補ごとに採用可否の対話を行う

template-candidate-review.mdを用い、候補ごとにAI初期見解→ユーザー見解→AI再考見解→合意決定の対話ループを行う。採用/却下/修正して採用のいずれかを決定する。

- ユーザー見解欄をAIが勝手に埋めてはならない
- AI再考見解は迎合であってはならない。ユーザー見解に同意する場合でも根拠を示す
- 候補が多い場合は3〜5件ずつに絞り、疲弊を避ける

---

## 出力形式

対象KnowledgeSchema documentのパスと状態遷移（DRAFT作成／審査結果）、および各候補の採用可否決定を報告する。

---

## ガードレール

- AIはACTIVE状態のknowledgeへ直接書き込まない。必ずDRAFT状態のKnowledgeSchema documentとして記録するに留める
- 個人の伝え方・コミュニケーションスタイルへのフィードバックは対象外とする（各AIツール自身の私的なフィードバック機構の管轄とし、このSkillの対象にしない）
- 候補の採用可否はユーザーとの対話を経て決定する。AIが単独で採用を決めない
- 審査の対話ループはknowledge-cultivator専用であり、汎用のbrainstorm skillとは独立した仕組みとして扱う。混同して同じ仕組みに載せない
- 採用決定後の昇格実行（status変更・validate・render）はこのSkillの責務外とする。Orchestratorが通常のCLI操作（CLAUDE.mdの運用ルール）として直接行う
- document.jsonの操作は必ずCLI/MCP経由で行う（直接Read/Edit/Writeしない）

---

## 参照

- `src/waffle/domain/model/KnowledgeSchema/v2.json`: knowledge候補を記録するためのschema。DRAFT/ACTIVEのstatusと、skillRefによるadvisor別deploy先制御を持つ。
- `.claude/skills/knowledge-cultivator/references/template-candidate-review.md`: 候補審査の対話ループ用テンプレート（このSkill専用、brainstormとは独立）。
- `docs/brainstorm/brainstorm-advisor-knowledge-growth.md`: このSkillの設計背景となったブレスト記録（8論点合意）。

---
name: "scrum-knowledge"
description: "Scrum・アジャイルに関する質問・設計判断・知識注入を行う際に使う。「Scrumの〜とは？」「PBIのリファインメントは誰が担うか？」「Sprint Goalとは？」などと言われたとき、またはAIエージェントに役割ごとのScrum責務を割り当てる設計でScrumの正確な知識が必要なときに使う。"
---

# Scrum・アジャイルに関する知識注入を行うSkill：scrum-knowledge

## 目的

Scrum・アジャイルに関する質問・設計判断・知識注入を行う際に使う。「Scrumの〜とは？」「PBIのリファインメントは誰が担うか？」「Sprint Goalとは？」などと言われたとき、またはAIエージェントに役割ごとのScrum責務を割り当てる設計でScrumの正確な知識が必要なときに使う。

---

## 役割

- Scrum Guideに定義された用語・役割・イベントを一次情報として提供する
- アジャイル12原則とScrumのマッピングを示す
- Scrumの役割（PO/SM/Dev/QA等）を担うAIエージェントが従うべき責務を明確にする

---

## 処理対象と成果物

### 処理対象

Scrumプロセス・役割・イベント・アーティファクトに関する質問、または設計判断への知識注入依頼。

### 成果物

Scrum Guide 2020とAgile Manifestoに基づく正確な知識の提供（Scrumの役割ごとにAIエージェントへ注入される情報源）。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| Scrumの概念・役割・イベント・アーティファクトについての質問、またはAIエージェントへのScrum知識注入依頼 | 質問の対象がPO/SM/Dev/QAいずれのAgentの責務に関わるか不明な場合は、references/usage-by-agent-role.mdの対応表を横断的に確認する。 |

---

## 実行手順

### Step 1: 質問・知識注入依頼の対象範囲を把握する

Scrumのどの概念・役割・イベントについての質問か、またはどのAgent種別向けの知識注入かを把握する。

### Step 2: 一次情報を参照する

references/knowledge/scrum-guide.mdおよびagile-manifesto.mdを一次情報として参照し、正確な定義・役割・原則を確認する。

### Step 3: 用語統一方針に従って回答する

references/terminology.mdの正式用語のみを使い、独自解釈を加えずScrum Guideの記述に基づいて回答する。

---

## 出力形式

Scrum Guideの内容は改変せず引用する形で回答する。

---

## ガードレール

- Scrum Guide の内容は改変せず引用する。独自解釈を加えない
- AIエージェントが担う責務と、現実のScrum Team が担う責務を混同しない
- AIエージェントは支援ツールであり、Scrumイベント自体を代替しない（Daily Scrum・Sprint Review等は人間が実施する）
- 同じ概念に対して複数の表現を使わない。references/terminology.mdの正式用語のみを使う

---

## 参照

- `.claude/skills/scrum-knowledge/references/knowledge/scrum-guide.md`: Scrum Guide 2020 全内容（定義・三本柱・価値基準・チーム構成・イベント・アーティファクト・コミットメント・Time-box）。
- `.claude/skills/scrum-knowledge/references/knowledge/agile-manifesto.md`: アジャイル宣言4つの価値＋12の原則＋Scrumとの対応表。
- `.claude/skills/scrum-knowledge/references/terminology.md`: 用語統一方針（正式用語と使用しない表現の対応表）。
- `.claude/skills/scrum-knowledge/references/usage-by-agent-role.md`: has-uddでの活用方針（PO/SM/Dev/QA Agentごとの参照知識）。

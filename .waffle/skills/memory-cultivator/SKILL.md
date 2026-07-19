---
name: "memory-cultivator"
description: "ユーザーによる訂正・重要な決定・参照情報など、将来のセッションやツールをまたいで再利用すべき事実に気づいたとき、またはユーザーから明示的に「覚えておいて」と頼まれたときに使う。ツールを問わず共有される.waffle/memory/へ、user/feedback/project/referenceの4種のいずれかとして記録する。"
---

# memory-cultivator

## 目的

ユーザーによる訂正・重要な決定・参照情報など、将来のセッションやツールをまたいで再利用すべき事実に気づいたとき、またはユーザーから明示的に「覚えておいて」と頼まれたときに使う。ツールを問わず共有される.waffle/memory/へ、user/feedback/project/referenceの4種のいずれかとして記録する。

---

## 役割

- ユーザーの訂正・重要な決定・参照情報の言及を検知し、user/feedback/project/referenceのいずれかに分類する
- 分類した内容を、対応するテンプレートに沿って.waffle/memory/配下へ記録する
- MEMORY.md索引を更新する
- 明示的な記録依頼があれば、検知トリガーを問わず即座に記録する

---

## 処理対象と成果物

### 処理対象

ユーザーによる訂正・重要な決定・参照情報の言及、または明示的な記録依頼

### 成果物

.waffle/memory/配下の記録ファイル（frontmatter付きMarkdown）と、更新されたMEMORY.md索引

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 検知トリガーの種別（自動検知された出来事か、明示的な依頼か） | 明示されなければ、直前の会話に「訂正」「決定」「覚えておいて」に相当する内容が含まれるかで判定する |
| 記録する型（user/feedback/project/referenceのいずれか） | 明示されなければ内容から推測する。user=ユーザー自身の役割・知識、feedback=approach是正・確認、project=進行中の意思決定・状況、reference=外部システムへのポインタ |

---

## 実行手順

### Step 1: 記録すべき出来事かを判定する

直前の会話が、ユーザーによる明示的な訂正・重要な決定・参照情報の言及・明示的な記録依頼のいずれかに該当するかを判定する。個人の伝え方・コミュニケーションスタイルへの指摘は対象外とする。

### Step 2: 記録する型を分類する

内容がuser/feedback/project/referenceのどれに該当するかを分類する。既存の.waffle/memory/内に関連する記録が既にあれば、新規作成ではなく更新を検討する。

### Step 3: テンプレートに沿って記録する

分類した型に対応するテンプレート（references/配下）を使い、frontmatter（name/description/metadata.type）と本文を記述する。feedback/project型は「事実→Why→How to apply」の構成を守る。

### Step 4: MEMORY.md索引を更新する

新規・更新した記録への1行ポインタをMEMORY.mdに追加・更新する。

---

## 出力形式

記録したファイルのパスと分類した型を報告する。

---

## ガードレール

- 既存の.claude/memory/（Claude Code専用の自動メモリ機構）への複製は行わない。新規メモリのみ.waffle/memory/へ書く
- AgentSchema等のdocument.json操作は必ずCLI経由（scaffold fill等）で行う。CLAUDE.md/AGENTS.mdを直接Edit/Writeしない
- advisorのバックボーンknowledgeへの追加候補の検知・審査はこのSkillの責務外。knowledge-cultivatorに委ねる
- 個人の伝え方・コミュニケーションスタイルへのフィードバックは対象外とする
- 採用可否の審査対話は行わない。訂正・実例に基づき最小限の記録を即座に行う

---

## 参照

- `references/template-user.md`: user型メモリのテンプレート（ユーザーの役割・知識・責務）
- `references/template-feedback.md`: feedback型メモリのテンプレート（是正・確認されたアプローチ、事実→Why→How to apply構成）
- `references/template-project.md`: project型メモリのテンプレート（進行中の意思決定・状況、事実→Why→How to apply構成）
- `references/template-reference.md`: reference型メモリのテンプレート（外部システムへのポインタ）

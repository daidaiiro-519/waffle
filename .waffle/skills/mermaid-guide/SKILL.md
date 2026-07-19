---
name: "mermaid-guide"
description: "Mermaidの構文パターンを参照・選択したいとき、図の表現方法を決めたいとき、Mermaidの記法を確認したいとき、またはknowledgeSkillsで図を作成するときに使う。「どのMermaid構文を使うか」「この図はどう書くか」「Mermaidで〜を表現したい」と言われたときに使う。"
---

# mermaid-guide

## 目的

Mermaidの構文パターンを参照・選択したいとき、図の表現方法を決めたいとき、Mermaidの記法を確認したいとき、またはknowledgeSkillsで図を作成するときに使う。「どのMermaid構文を使うか」「この図はどう書くか」「Mermaidで〜を表現したい」と言われたときに使う。

---

## 役割

- 図の内容・目的に応じた最適なMermaid構文を選定する
- 各構文の基本テンプレートと実例を提供する
- Skills間で統一されたMermaid記法を保証する

---

## 処理対象と成果物

### 処理対象

表現したい図の内容・目的（他Skillsからの参照を含む）。

### 成果物

選定した構文のテンプレートに従って生成したMermaid図。

---

## 入力の想定

| 受け取る情報 | 解釈・既定値 |
|---|---|
| 表現したい図の内容・目的 | 対応する構文が不明な場合はreferences/syntax-overview.mdの選択基準に従って判定する。 |

---

## 実行手順

### Step 1: 構文を選定する

references/syntax-overview.mdを読み込み、表現したい内容に対応する構文を特定する。

### Step 2: パターンファイルを読み込む

特定した構文のreferences/pattern-{構文名}.mdを読み込み、テンプレートと実例を参照する。

### Step 3: 図を生成する

パターンファイルのテンプレートに従って図を生成する。

---

## ガードレール

- graph構文は使用しない。フローチャートは必ずflowchartを使う（旧構文のため）
- 判断フロー（YES/NO分岐）はMermaidではなくテキスト形式（コードブロック）で表現する
- beta構文（sankey-beta, xychart-beta, architecture-beta, block-beta）は表示環境に依存するため、使用時は注意を促す

---

## 参照

- `.claude/skills/mermaid-guide/references/syntax-overview.md`: 全構文一覧と選択基準。
- `.claude/skills/mermaid-guide/references/pattern-flowchart.md`: フローチャート。
- `.claude/skills/mermaid-guide/references/pattern-sequence.md`: シーケンス図。
- `.claude/skills/mermaid-guide/references/pattern-class.md`: クラス図。
- `.claude/skills/mermaid-guide/references/pattern-er.md`: ER図。
- `.claude/skills/mermaid-guide/references/pattern-state.md`: 状態遷移図。
- `.claude/skills/mermaid-guide/references/pattern-quadrant.md`: 象限チャート。
- `.claude/skills/mermaid-guide/references/pattern-mindmap.md`: マインドマップ。
- `.claude/skills/mermaid-guide/references/pattern-timeline.md`: タイムライン。
- `.claude/skills/mermaid-guide/references/pattern-journey.md`: ユーザージャーニー。
- `.claude/skills/mermaid-guide/references/pattern-gantt.md`: ガントチャート。
- `.claude/skills/mermaid-guide/references/pattern-pie.md`: 円グラフ。
- `.claude/skills/mermaid-guide/references/pattern-git.md`: Gitグラフ。
- `.claude/skills/mermaid-guide/references/pattern-requirement.md`: 要件図。
- `.claude/skills/mermaid-guide/references/pattern-sankey.md`: サンキー図（beta）。
- `.claude/skills/mermaid-guide/references/pattern-xychart.md`: XYチャート（beta）。
- `.claude/skills/mermaid-guide/references/pattern-block.md`: ブロック図（beta）。
- `.claude/skills/mermaid-guide/references/pattern-architecture.md`: アーキテクチャ図（beta）。

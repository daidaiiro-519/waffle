# require-query-before-array-fill

## 目的

配列フィールドを含むscaffold fillを実行する前に、同じ対象パスへwaffle queryが先行実行されているかを確認する運用ルール（CLAUDE.mdの「配列はqueryで現在値取得→組み立て→fillで丸ごと置き換え」）を機械的に強制する。

---

## いつ働くか

Bash経由でwaffle scaffold fillが配列フィールドを含んで実行される直前

---

## 委譲先usecase

check-query-precedes-array-fill

---

## スクリプト実体

.waffle/hooks/require-query-before-array-fill.py

---

## ガードレール

- 判定ロジックをこのHookスクリプトに持ち込まない。transcriptパース等の技術的詳細のみをこのスクリプトが担い、allow/denyの判定自体はusecaseRefが指すusecaseで行う

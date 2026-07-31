---
id: "require-handoff-before-implementation"
type: "self-contained"
title: "require-handoff-before-implementation"
description: "CLAUDE.mdが定めるフルサイクル（調べる→決める→引き継ぐ→作る）のうち、引き継ぎ工程を飛ばして実装に着手する事故を防ぐ。specを書き終えた直後は成果物が積み上がって手が動く状態になり、Handoffの存在を確認せずコードへ進みやすい。"
schemaRef: "HookSchema/v1"
---

# require-handoff-before-implementation

## 目的

CLAUDE.mdが定めるフルサイクル（調べる→決める→引き継ぐ→作る）のうち、引き継ぎ工程を飛ばして実装に着手する事故を防ぐ。specを書き終えた直後は成果物が積み上がって手が動く状態になり、Handoffの存在を確認せずコードへ進みやすい。

---

## いつ働くか

Skillパッケージ配下の実装ファイル（スクリプト・インフラ定義・雛形HTML等）をEdit/Writeで書き込んだ直後。

---

## 判定ロジック

書き込み先が .waffle/skills/<スキル名>/ 配下の実装ファイルかを判定する。SKILL.md・README.md・references配下の文書は対象外とし、references/templates直下のHTML（配信画面の実体）だけは実装として扱う（templates/doc配下は共有される文書の雛形なので対象外）。該当する場合、そのスキルがフルサイクルに入っているか（.waffle/documents/specs/bc-<スキル名>/ にドメイン仕様があるか）を確認し、仕様が無ければ何もしない。仕様がある場合に限り、そのスキル名を含む Handoff document が .waffle/documents/handoff/ に存在するかを探し、見つからなければ引き継ぎ工程を飛ばしている可能性を通知する。ブロックはしない。

---

## スクリプト実体

.claude/hooks/require-handoff-before-implementation.py

---

## ガードレール

- ブロックしない（通知のみ）。Handoffが不要な軽微な修正も実在するため、判断の余地を残す
- Handoffの有無だけを見る。中身が十分かどうかは判定しない（AI自身が証跡を書けてしまう以上、どんな指標も自己申告の域を出ないため）
- ドメイン仕様を持たないSkillは対象外とする。試作として作られたものを鳴らし続けると雑音になり、通知そのものが無視されるようになる
- SKILL.md と references配下の文書は対象外とする。これらは仕様・知識の成果物であり実装ではない
- 新しい判定ロジックをここに増やさない。工程の抜けを気づかせることだけを担う

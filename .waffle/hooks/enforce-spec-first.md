# enforce-spec-first

## 目的

spec-first原則（idea→ブレスト→spec→実装）に沿わずschema実装へ飛びつく傾向を、書き込み後に気づける形で記録する。

---

## いつ働くか

新規schemaファイル（src/waffle/domain/model/配下のv*.json）への書き込み直後

---

## 判定ロジック

新規schemaファイル（src/waffle/domain/model/*/v*.json）が書き込まれた後、それを参照するstatus=VALIDATED以上のspecが.waffle/documents/specs配下に見つからなければ通知する（ブロックしない）。Waffle自身の運用を支えるインフラ・ツール系schemaはusecaseを持つ必然性が無く、正当な理由でVALIDATED specが存在しないままschemaを書くケースが実在するため、機械的な自己申告検証には限界があるとの判断からブロックではなく通知に留めている。

---

## スクリプト実体

.waffle/hooks/enforce-spec-first.py

---

## ガードレール

- ブロッキングにしない（「合意済みか」はtool_inputの中身だけからは原理的に検証できないため）
- インフラ・ツール系schemaでは正当な理由で発火することがある。発火=違反と機械的に断定しない

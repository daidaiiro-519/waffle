---
id: "pre-bash-dispatch"
type: "self-contained"
title: "pre-bash-dispatch"
description: "PreToolUse:BashのHookが実質2本（protect-raw-json-access.pyのBash分岐、require-query-before-array-fill.py）に分かれて個別に起動していたため、Bashコマンド1回あたりのプロセス起動数が不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。2本の判定ロジック・拒否理由の文言は変更せず、プロセス起動だけを1本に集約する。"
schemaRef: "HookSchema/v1"
---

# pre-bash-dispatch

## 目的

PreToolUse:BashのHookが実質2本（protect-raw-json-access.pyのBash分岐、require-query-before-array-fill.py）に分かれて個別に起動していたため、Bashコマンド1回あたりのプロセス起動数が不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。2本の判定ロジック・拒否理由の文言は変更せず、プロセス起動だけを1本に集約する。

---

## いつ働くか

Bashツールの実行直前

---

## 判定ロジック

protect-raw-json-access.pyとrequire-query-before-array-fill.pyをimportlib経由で動的importし、それぞれが持つBash用の判定関数（check_bash(payload)、check(payload, transcript_text)）を順に呼び出す。いずれかがNoneでない拒否理由の文字列を返した時点で、それ以降の関数は呼ばずpermissionDecision=denyとして即座にその理由を返す。両方ともNone（許可）を返した場合は何も出力せず終了する。

---

## スクリプト実体

.claude/hooks/pre-bash-dispatch.py

---

## ガードレール

- 新しい判定ロジックをここに持ち込まない。protect-raw-json-access.pyのBash用関数とrequire-query-before-array-fill.pyの判定関数を順に呼び出し、最初に見つかった拒否理由を返すだけの集約ディスパッチャである
- protect-raw-json-access.pyのRead用チェックはこのディスパッチャの対象外。PreToolUse:Readのmatcherは引き続きprotect-raw-json-access.py単体で処理する
- 既存2ファイルは削除しない。それぞれ単体でも判定関数を持つモジュールとして残し、settings.jsonのPreToolUse:Bashエントリだけをこのディスパッチャに差し替える

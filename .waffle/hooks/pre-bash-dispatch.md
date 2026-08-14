---
id: "pre-bash-dispatch"
type: "self-contained"
title: "pre-bash-dispatch"
description: "PreToolUse:BashのHookが個別に起動し、Bashコマンド1回あたりのプロセス起動数が不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。委譲先それぞれの判定ロジック・拒否理由の文言は変更せず、プロセス起動だけを1本に集約する。委譲先の数はこのHookのbehaviorが正であり、ここには数を書かない——数え上げは、増減したときに定義のほうが古くなる。"
schemaRef: "HookSchema/v1"
---

# pre-bash-dispatch

## 目的

PreToolUse:BashのHookが個別に起動し、Bashコマンド1回あたりのプロセス起動数が不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。委譲先それぞれの判定ロジック・拒否理由の文言は変更せず、プロセス起動だけを1本に集約する。委譲先の数はこのHookのbehaviorが正であり、ここには数を書かない——数え上げは、増減したときに定義のほうが古くなる。

---

## いつ働くか

Bashツールの実行直前

---

## 判定ロジック

protect-raw-json-access.py・require-query-before-array-fill.py・refuse-write-into-outdated-schema.py をimportlib経由で動的importし、それぞれが持つBash用の判定関数（check_bash(payload)、check(payload, transcript_text)、check(payload)）を宣言した順に呼び出す。いずれかがNoneでない拒否理由の文字列を返した時点で、それ以降の関数は呼ばずpermissionDecision=denyとして即座にその理由を返す。すべてNone（許可）を返した場合は何も出力せず終了する。

---

## スクリプト実体

.claude/hooks/pre-bash-dispatch.py

---

## ガードレール

- 新しい判定ロジックをここに持ち込まない。委譲先それぞれの判定関数を順に呼び出し、最初に見つかった拒否理由を返すだけの集約ディスパッチャである
- 呼び出す委譲先を増やしたときは、このHookの宣言を先に直す。宣言が「2本を呼ぶ」のまま実装だけ3本にした結果、宣言と実装が食い違ったまま気づかれない状態が生じた
- protect-raw-json-access.pyのRead用チェックはこのディスパッチャの対象外。PreToolUse:Readのmatcherは引き続きprotect-raw-json-access.py単体で処理する
- 委譲先のファイルは削除しない。それぞれ単体でも判定関数を持つモジュールとして残し、settings.jsonのPreToolUse:Bashエントリだけをこのディスパッチャに差し替える

---
id: "post-bash-dispatch"
type: "self-contained"
title: "post-bash-dispatch"
description: "PostToolUse:BashのHookが3本（check-drift-on-write.py／notify-advisor-consultation.py／notify-validate-render-after-write.py）に分かれて個別に起動し、そのうち2本が同一のtranscriptファイルを独立に全読みしていたため、Bashコマンド1回あたりのプロセス起動数・I/Oが不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。3本の判定ロジック・責務・通知文言は変更せず、プロセス起動とtranscript読み込みだけを1本に集約する。"
schemaRef: "HookSchema/v1"
---

# post-bash-dispatch

## 目的

PostToolUse:BashのHookが3本（check-drift-on-write.py／notify-advisor-consultation.py／notify-validate-render-after-write.py）に分かれて個別に起動し、そのうち2本が同一のtranscriptファイルを独立に全読みしていたため、Bashコマンド1回あたりのプロセス起動数・I/Oが不必要に重複していた（tech-lead-advisor敵対的検証で指摘）。3本の判定ロジック・責務・通知文言は変更せず、プロセス起動とtranscript読み込みだけを1本に集約する。

---

## いつ働くか

Bashツールの実行直後

---

## 判定ロジック

対象のtranscript_pathを1回だけ読み込む（読み込めない場合は空文字列として扱う）。check-drift-on-write.py・notify-advisor-consultation.py・notify-validate-render-after-write.pyの3ファイルをimportlib経由で動的importし、それぞれが持つcheck(payload)またはcheck(payload, transcript_text)関数を、読み込み済みのtranscript_textを渡して呼び出す。各関数はNoneまたは通知メッセージ文字列を返す仕様とする。Noneでない結果が1つ以上あれば、それらを改行で連結してadditionalContextとして1回だけ通知する。全てNoneであれば何も出力せず終了する。3関数の判定基準・通知文言そのものは変更しない（プロセス統合のみが目的）。

---

## スクリプト実体

.claude/hooks/post-bash-dispatch.py

---

## ガードレール

- 新しい判定ロジックをここに持ち込まない。既存3Hook（check-drift-on-write.py／notify-advisor-consultation.py／notify-validate-render-after-write.py）のcheck関数を呼び出して結果を連結するだけの集約ディスパッチャである
- 既存3ファイルは削除しない。それぞれ単体でも判定関数を持つモジュールとして残し、settings.jsonのPostToolUse:Bashエントリだけをこのディスパッチャに差し替える（PostToolUse:Edit|Writeのcheck-drift-on-write.py単体呼び出しは維持する）
- 3関数の呼び出し順序・結果の並び順を仕様として固定しない（重要度順であることを保証しない）

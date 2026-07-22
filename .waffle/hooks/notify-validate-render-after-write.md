---
id: "notify-validate-render-after-write"
type: "self-contained"
title: "notify-validate-render-after-write"
description: "process-reliability論点3（brainstorm-waffle-process-reliability.md）の残り部分。Bash経由でwaffle scaffold fill / patch-schemaがdocument.json・schema.jsonを書き換えた後、対応するwaffle validate・waffle renderが同一セッション内で実行されたかを確認する。fillはdocument.jsonを更新するが、validate/renderを怠るとレンダリング済み成果物（.md/.html等）がsourceとズレたまま気づかれず、Waffleの差別化原理（陳腐化しない仕様）を損なう。"
schemaRef: "HookSchema/v1"
---

# notify-validate-render-after-write

## 目的

process-reliability論点3（brainstorm-waffle-process-reliability.md）の残り部分。Bash経由でwaffle scaffold fill / patch-schemaがdocument.json・schema.jsonを書き換えた後、対応するwaffle validate・waffle renderが同一セッション内で実行されたかを確認する。fillはdocument.jsonを更新するが、validate/renderを怠るとレンダリング済み成果物（.md/.html等）がsourceとズレたまま気づかれず、Waffleの差別化原理（陳腐化しない仕様）を損なう。

---

## いつ働くか

Bash経由のwaffle scaffold --operation fillまたはwaffle patch-schemaの実行直後

---

## 判定ロジック

このHookはfill/patch自体の実行直後には発火しない（validate/renderはまだ未来のコマンドで、その時点では必ず「未実行」判定になり無意味な通知になるため）。代わりに、transcript内のBashコマンド列を辿り、fill/patch-schemaで書き換えた対象（--pathまたは--schemaRef）を記録する。その後、同じ対象への追加fillが続く間は「まとめて後でvalidate/renderする運用」として何もしない。対象が別のtargetへ切り替わった時点（＝直前の対象への作業が一区切りついたとみなせるタイミング）で、直前の対象に対してwaffle validate・waffle renderの両方の呼び出しが間に挟まっていたかを確認する。どちらか（または両方）が見つからなければ、不足しているコマンド名を含めてadditionalContextとして通知する（ブロックはしない）。transcriptからコマンド列を抽出する際、heredocの本体やコメント行に書かれた文字列（実行されていないコマンド例等）は判定対象から除外する。

---

## スクリプト実体

.claude/hooks/notify-validate-render-after-write.py

---

## ガードレール

- 新しいdrift検知ロジックをこのHookスクリプトに持ち込まない（check-drift-on-write.pyの責務と混同しない）。ここで確認するのはコマンドの実行有無のみで、内容の正しさは判定しない
- ブロックしない（PostToolUse通知のみ）。process-reliability論点1と同じ、通知に留める運用方針を踏襲する
- 同一documentPathに対する複数回のfillをまとめて1回のvalidate/renderで済ませる運用を妨げない（fillのたびに毎回通知するのではなく、最後のfillから見て後続にvalidate/renderがあるかで判定する）

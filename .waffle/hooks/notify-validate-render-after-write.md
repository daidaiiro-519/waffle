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

検知したfill/patchコマンドから対象のdocumentPath（またはschemaRef）を抽出する。同一transcript内で、その後に対象と同じpathを指すwaffle validateコマンド、およびwaffle renderコマンドの呼び出しがあるかを確認する。両方揃っていれば沈黙する。どちらか（または両方）が見つからなければ、不足しているコマンド名を含めてadditionalContextとして通知する（ブロックはしない）。

---

## スクリプト実体

.claude/hooks/notify-validate-render-after-write.py

---

## ガードレール

- 新しいdrift検知ロジックをこのHookスクリプトに持ち込まない（check-drift-on-write.pyの責務と混同しない）。ここで確認するのはコマンドの実行有無のみで、内容の正しさは判定しない
- ブロックしない（PostToolUse通知のみ）。process-reliability論点1と同じ、通知に留める運用方針を踏襲する
- 同一documentPathに対する複数回のfillをまとめて1回のvalidate/renderで済ませる運用を妨げない（fillのたびに毎回通知するのではなく、最後のfillから見て後続にvalidate/renderがあるかで判定する）

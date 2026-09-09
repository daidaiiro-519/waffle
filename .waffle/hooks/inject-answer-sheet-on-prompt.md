---
id: "inject-answer-sheet-on-prompt"
type: "self-contained"
title: "承認の画面から届いた回答を、次の発言のときに読ませるHook：inject-answer-sheet-on-prompt"
description: "承認の画面で押した回答はファイルに落ちるが、Claude Code は自分からターンを始められないため、そのままでは誰も読まない。利用者が次に何か書いたとき、まだ読んでいない回答だけを文脈へ入れることで、『回答を読んで』と毎回書かせずに済むようにする。"
schemaRef: "HookSchema/v1"
---

# 承認の画面から届いた回答を、次の発言のときに読ませるHook：inject-answer-sheet-on-prompt

## 目的

承認の画面で押した回答はファイルに落ちるが、Claude Code は自分からターンを始められないため、そのままでは誰も読まない。利用者が次に何か書いたとき、まだ読んでいない回答だけを文脈へ入れることで、『回答を読んで』と毎回書かせずに済むようにする。

---

## いつ働くか

利用者が何か書いて送ったとき（Claude Code: UserPromptSubmit）

---

## 判定ロジック

回答の置き場（.waffle/answers/）にあるファイルのうち、既読の印（.waffle/answers/.read）より新しいものだけを拾う。1件も無ければ何も出力せず沈黙する。在れば、各ファイルの board・answeredAt と、問いごとの questionId・verdict・returnReason・note を並べて追加の文脈として出し、そのファイル名を既読の印へ書き足す。壊れた JSON は読み飛ばし、その旨だけを1行で出す。

---

## スクリプト実体

.waffle/hooks/inject-answer-sheet-on-prompt.py

---

## ガードレール

- 回答が0件のときは何も出力しない（沈黙する）
- 既読にしたものを二度と出さない。同じ回答が毎回文脈へ入ると、古い諾否で作業を進めることになる
- 回答ファイルを消さない・書き換えない。既読の管理は別ファイル（.waffle/answers/.read）で行う
- 判定ロジックを増やさない。読むのは形の決まった欄だけで、note の中身は解釈せずそのまま渡す
- 壊れた JSON で止まらない。読み飛ばして、読み飛ばしたことだけを伝える

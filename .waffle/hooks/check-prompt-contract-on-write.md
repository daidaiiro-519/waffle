---
id: "check-prompt-contract-on-write"
type: "usecase-delegate"
title: "check-prompt-contract-on-write"
description: "スキーマが書かれた直後に、指示の置かれ方の契約が守られているかを確かめる。引く単位に x-prompt-query があること、値を書き込む欄に x-prompt-write があること、そして契約が認める名前はこの2つだけであること。指示が抜けたまま気づかないと、その欄を埋める側はガイダンス無しで値を決めることになり、埋める者ごとに違うものが入る。読まれない名前で置かれた指示は、書いた本人にも気づけない。"
schemaRef: "HookSchema/v1"
---

# check-prompt-contract-on-write

## 目的

スキーマが書かれた直後に、指示の置かれ方の契約が守られているかを確かめる。引く単位に x-prompt-query があること、値を書き込む欄に x-prompt-write があること、そして契約が認める名前はこの2つだけであること。指示が抜けたまま気づかないと、その欄を埋める側はガイダンス無しで値を決めることになり、埋める者ごとに違うものが入る。読まれない名前で置かれた指示は、書いた本人にも気づけない。

---

## いつ働くか

waffle patch-schema が実行された直後。スキーマへの正規の書き込み経路はこれだけなので、新規のブロック追加でも既存の書き換えでも必ずここを通る。実際の配線は settings.json の PostToolUse:Bash（post-bash-dispatch 経由）が正本で、この記述はその意図の説明。

---

## 委譲先usecase

check-prompt-contract

---

## スクリプト実体

.waffle/hooks/check-prompt-contract-on-write.py

---

## ガードレール

- 新しい判定ロジックをこのHookスクリプトに持ち込まない。規則の追加・変更はusecase側で行う（2箇所に分かれるとやがて食い違う）
- 契約が守られているときは沈黙する。毎回鳴る警報は鳴らない警報と同じになる
- 指示の中身が指示として適切かは判定しない。置かれ方だけを見る

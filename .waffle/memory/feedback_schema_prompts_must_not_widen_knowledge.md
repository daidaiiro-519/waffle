---
name: schema-prompts-must-not-widen-knowledge
description: schemaの記入指示がknowledgeの定義より広い許可を出すと、違反が仕様として通る。ただし広いかどうかはknowledgeの定義を全文読んでから言う
metadata:
  node_type: memory
  type: feedback
---

schema の記入指示（x-prompt-write）や discriminator が、**knowledge の定義より広い許可を出してはいけない**。広げると、knowledge が排除するものが仕様として正当に通り、以後どの検査にも引っかからなくなる。導出の向きは knowledge → x-prompt であり、逆流させない。

**Why:** `HookSchema/v1` の `self-contained` が実例。「フックは判断であれ配線であれ仕様で管理する」というユーザーの明示に対し、判断を持つフックが散文の欄だけで通る道を作っていた。その場の実測（「実際に4件が完結型だった」）を根拠に許可を広げた形で、方針が唯一の正であり実測は方針に照らして判定される対象である、という順序が逆転していた。

**この原則を当てはめるときの落とし穴（実際に踏んだ）:** 「広いかどうか」は、knowledge の**定義の全文**を読んでから言う。私は `DomainSpecSchema` の記入指示を抜け穴だと断じたが、根拠にした定義を後半だけしか読んでいなかった（定義は「〜または〜」の二択で、前半を落としていた）。**半分だけ読んだ判定を「実測で確認済み」として記録すると、その誤りが次のセッションの前提になる。** 広いと断じる前に、定義の本文・判断の木・表を全部当たる。関連: [[feedback_read_all_standards_not_one_block]] [[skip-confirmation-before-acting]]

**How to apply:** schema を書く・改訂するときは、記入指示と enum・discriminator が knowledge の定義より広くないかを照合する。「〜なら空でよい」「〜の場合はこの種別」という**免除の文言を書こうとしている瞬間が合図**——ただし合図は調べ始める合図であって、断じてよい合図ではない。判定は knowledge が持ち、schema は形だけを持つ。

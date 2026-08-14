---
name: schema-prompts-must-not-widen-knowledge
description: schemaの記入指示がknowledgeの定義より広い許可を出すと、違反が仕様として通る。抜け穴はschema側に生える
metadata:
  node_type: memory
  type: feedback
---

schema の記入指示（x-prompt-write）や discriminator が、**knowledge の定義より広い許可を出してはいけない**。広げると、knowledge が排除するものが仕様として正当に通り、以後どの検査にも引っかからなくなる。

**Why:** 同じ形の抜け穴を2つ実測した。(1) `HookSchema/v1` の `self-contained` ——「フックは仕様で管理する」に対し、判断を持つフックが `behavior` の散文だけで通る道を作った（15件中8件が使用、うち6件は判断を持つ）。(2) `DomainSpecSchema` の `referencedAggregates` の記入指示「測る対象が集約の外にあるなら空のままでかまいません」——knowledge の定義は「業務サービス＝**複数の集約にまたがる**状態を持たない計算」なのに、集約をまたがない計算を業務サービスとして宣言できてしまう（既存6件中2件が該当）。どちらも、その場の実測（「実際に4件が完結型だった」）を根拠に許可を広げている。方針が唯一の正で、実測は方針に照らして判定される対象である（[[knowledge-cand-policy-is-ssot-measurement-is-judged]]）。

**How to apply:** schema を書く・改訂するときは、記入指示と enum・discriminator が knowledge の定義より広くないかを照合する。広い許可を書きたくなったら、それは knowledge のほうを直すべき事案か、あるいは分類そのものが間違っている事案。「〜なら空でよい」「〜の場合はこの種別」という**免除の文言を書こうとしている瞬間が合図**。判定は knowledge が持ち、schema は形だけを持つ。関連: [[feedback_hooks_are_spec_managed_without_exception]] [[feedback_evidence_based_scope_misapplication]]

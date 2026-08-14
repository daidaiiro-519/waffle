---
name: no-concrete-identifiers-in-abstraction-records
description: 抽象の在り方を決める記録の主要な欄に、個別の識別子や綴りを並べない
metadata:
  node_type: memory
  type: feedback
---

仕様の抽象度・持ち分・境界を決める記録では、決定・変更前後・理由・軸の各欄に**個別の識別子（フィールド名・クラス名・基準の id）を置かない**。実例が要るなら、折りたたみの裏付け欄に参照先として置く。

**Why:** 仕様と規約の分け目を決める ADR で、`operationName` や `bullet-wins-over-join` を変更前後の表と理由の連鎖に並べた。ユーザーの指摘「なぜここの話で具体の operation name の名前などが出てくるんですか？」。**具体を抽象の側に置かないことを決めようとしている記録が、まさにそれをやっていた。** さらに実害があり、個別の綴りを主語にしたことで、決定そのものが「特徴をどちらの箱へ入れるか」という仕分けの規則にすり替わっていた。決めるべきだったのは仕様がどこまでを持つかである。

**How to apply:** 抽象の話をする記録では、主要な欄の主語を**測り方・範囲・関係**に保つ。識別子を書きたくなったら、それが決定の主語なのか、決定を当てた結果の実例なのかを問う。実例なら折りたたみへ降ろす（[[information-before-or-after-by-reading-need]] の「疑ったときに要る情報は後ろ」に当たる）。なお実例を裏付けとして引くこと自体は必要で、避けるのは実例を主語に据えることである。関連: [[abstraction-is-not-reduction]] [[find-the-gap-knowledge-left-open]] [[no-pattern-names-in-spec-vocabulary]]

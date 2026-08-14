---
name: find-the-gap-knowledge-left-open
description: 決定を書く前に、その論点で knowledge が既に持っている部分と、意図して空けている部分を分ける
metadata:
  node_type: memory
  type: feedback
---

決定を起こすとき、まず該当 knowledge の**原則**と**留保事項**を両方読み、次の3つに分ける。

| 分類 | 決定が何をすべきか |
|---|---|
| knowledge が既に持っている | **決め直さない。**引くだけ |
| knowledge が意図して空けている | **ここを埋める。**これが決定の対象 |
| knowledge に無く、空けてもいない | Waffle の設計判断として置く。該当なしと明記する |

留保事項（caveats）は「まだ書けていないこと」ではなく、**どこが決定に開かれているかの目印**として読む。

**Why:** 仕様と規約の分け目を決めようとして、`spec-describes-behavior-not-implementation` が既に持っている**上限**（記述から手段の名前を取り除いて意味が保たれるかで測る）を、自分の言葉で決め直そうとした。ユーザーの指摘「決定に対する他の欄があまりにずれてます」。読み直すと、留保事項が空けているのは**下限**だけだった——「どこまで抽象化すると読み手が理解できなくなるかという下限は、文書の読み手によって変わるため、一律の基準を置いていない」。決定の対象を下限に絞ると、理由も軸も変更前後も自ずと揃った。**欄がずれるのは書き方の問題ではなく、決定の対象を取り違えている合図である。**

**How to apply:** ADR の理由の連鎖の第1段を、原則として「knowledge のここが空いている」という実測から始める。空いている場所を名指しできないなら、まだ決定の対象が定まっていない。あわせて、空いている理由も読む——`spec-describes-behavior-not-implementation` は「読み手によって変わるから」空けていた。**空けた理由を消せば埋められる**（測る相手を読み手から導出へ移した）。関連: [[abstraction-is-not-reduction]] [[no-concrete-identifiers-in-abstraction-records]] [[schema-prompts-must-not-widen-knowledge]]

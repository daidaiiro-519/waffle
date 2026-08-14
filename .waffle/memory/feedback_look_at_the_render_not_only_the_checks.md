---
name: look-at-the-render-not-only-the-checks
description: 成果物は自動検査の合否だけで確認したと言わない。実際の描画を見てから報告する
metadata:
  node_type: memory
  type: feedback
---

HTMLやSVGを出すとき、**自動検査を通しただけで「確認済み」と報告しない**。描画を画像として取り込み、目で見てから報告する。

自動検査が見ないもの:

| 見ない | 実際に起きたこと |
|---|---|
| 中身が意味として壊れているか | CSSを行単位で抜き出したため、無関係な規則の途中行が混ざり、変数定義が selector の外に落ちていた。はみ出しも重なりも無いので検査は通る |
| 図と本文の食い違い | 図の要素は5つ、本文は「6種類」。数え直すと内訳も5つだった |
| 溢れたときにどちらが切れるか | `justify-content:center` で溢れた図は左右が均等に切れ、左端へスクロールできない |
| 明暗への追随 | 図の変数が明るい側だけを持ち、暗い画面で図だけ明るいまま残っていた |

**Why:** ユーザーの指摘「図が壊れてますね」。私は直前に「表示は3通り（広い・狭い・暗い）で確認済み」と報告していたが、**通したのは重なり・はみ出しの検査だけで、描画は一度も見ていなかった**。検査スクリプト自身が出力の末尾で「Open each PNG and look at it. The checks above do not see collisions between lines and text, crowding, or a diagram that is merely unclear.」と告げていたのに、その行を読み飛ばしていた。

**How to apply:** 描画を伴う成果物は、公開前に screenshot を取って Read で開く。狭い・暗いも含める。「検査を通した」は「確認した」ではない——**報告に使ってよいのは、見たものだけ**。あわせて、既存の成果物から部品（CSS・図）を持ち出すときは、行単位ではなく構文の単位（波括弧を数えて規則ごと）で取り出す。関連: [[every-column-leads-with-its-conclusion]] [[skip-confirmation-before-acting]]

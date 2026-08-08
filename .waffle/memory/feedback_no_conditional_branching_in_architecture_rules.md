---
name: feedback_no_conditional_branching_in_architecture_rules
description: フォルダ構成はアーキテクチャ規約が直接1つ宣言する。分類による場合分けを規約へ持ち込まない
metadata:
  type: feedback
---

フォルダ構成は各アーキテクチャ規約（`conceptPlacement`）が直接1つ宣言する。「中核なら概念ごとに分ける／補完なら分けない」のような**分類による場合分けを規約へ持ち込まない**。2026-08-08、`thicknessBySubdomain` に「概念ごとに置き場所を分けるか」の欄を足す提案をして却下された。

**Why:** ユーザーの言葉は「フォルダ構成はアーキテクチャ規約で決まった段階からそこに概念の場合分けが入るのはしゃばい」。具体的に何が壊れるか——`architecture-waffle` は1つの文書の中に `thicknessBySubdomain` の3分類（中核・一般・補完）を全部持ち、`conceptPlacement` は1つしか持たない。つまり1つのアーキテクチャが分類の違う領域をまとめて受け持つ前提。そこへ分類ごとの分岐を入れると、1つの文書の中でフォルダ構成が分岐し、「どの領域のコードか」を判定しないと置き場所が決まらなくなる。検査も同じ分岐を持つことになる。

いま分岐は無い。`architecture-waffle` は value-object → `domain/value_objects`、`architecture-artifact-share` は value-object → `domain` と、それぞれが直接1つ宣言している。2つのプロジェクトで形が違うのは2つの文書が違うことを宣言しているからで、それ以上の説明を足す必要がない。

**How to apply:** 「2つのプロジェクトで形が違う」を見つけても、それを統一する上位規則を作ろうとしない。違いが各アーキテクチャ規約の宣言として既に表れているなら、そこで完結している。規約に導出規則（Xから Y を計算する）を足す提案をする前に、その規約が単一の文書の中で複数の分類を束ねていないか確認する。束ねているなら、その導出規則は文書内で分岐を生む。

関連: [[project_domain_folder_unit_is_kind_based]]（種類単位で確定した経緯）、[[feedback_evidence_based_scope_misapplication]]（過剰な一般化を避ける同型の判断）

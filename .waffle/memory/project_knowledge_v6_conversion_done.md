---
name: project_knowledge_v6_conversion_done
description: ddd-advisor の knowledge 19本を書き起こし版から KnowledgeSchema/v6 へ全件変換完了（2026-08-11）
metadata:
  type: project
---

ddd-advisor のバックボーン knowledge 19本を、書き起こし版（`.waffle/skills/ddd-advisor/references/archive/knowledge-v1-book-transcription/`、4,750行）から `KnowledgeSchema/v6` の概念の木へ**全件変換した**（2026-08-11）。

**結果**: 旧要約版1,997行 → 5,533行（2.8倍）。450ノード・図80・原文30。

**旧要約版が落としていたもの**: 図は19本すべてで0だった。器（原則・分類・判断基準・実例・アンチパターン）に図を入れる場所が無く、型に合うものだけが残っていた。コードも同様に全滅（domain-model 7本・event-sourced-domain-model 7本）。

**途中で変えた形**（どちらも仕様→x-prompt→document の順で直した）:
1. Markdown の原文がコード塊に囲われて表として読めない → `verbatim-is-rendered-as-source` に「宣言された種類が描画の出力形式そのものであるとき、囲わずにそのまま置く」を追加
2. 図の後ろの辺の一覧表（から／へ／関係）が図の書き写しでしかない → `figure.notes` へ入れ替え（[[project_figure_notes_table]]）

**著作権対応**: 実例・企業名・製品名・人名・比喩に由来する呼び名・法令名をすべて置き換え、構造だけ保った（[[feedback_replace_book_examples_in_conversion]]）。変換のたびに grep で0件を確認済み。

**既知の残り**: `subdomain` の分類マトリクス（4象限）だけ注釈が無い。4象限の図に対応する描画の種類が無いため原文として持たせており、注釈の表は図の宣言にしか付かない。意図と読み取りの文章に4象限すべての説明は入っている。

アーティファクト19本（`docs/adr/knowledge-conversion-*.html`）に、各本の差分と完全プレビューを記録した。

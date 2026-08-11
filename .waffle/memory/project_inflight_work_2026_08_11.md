---
name: project_inflight_work_2026_08_11
description: 2026-08-11時点で走っている作業の連鎖と、どこで止まっているか。サブドメインの是正から knowledge の器の話へ脱線した経緯を含む
metadata:
  type: project
---

2026-08-11。作業が連鎖して深くなったので、着手順と現在地を残す。**上から順に戻ればよい。**

## いま止まっている場所

**KnowledgeSchema の器の作り直し**。書き起こし版19本（4,750行）が「概念の木」なのに、KnowledgeSchema は「1文書＝1概念、固定ブロックが平ら」なので、木の枝（手順・関係の説明）が落ちる。見出し372件のうち61%が現ブロック語彙に落ちない。深さは最大4（#〜####）、本文に表164行・コードブロック258・mermaid 43。方向として「概念のノードを有界に再帰させる」を提案し、本文をMarkdownのまま持つか構造化するかの判断待ち。

## 連鎖の全体（上ほど元の目的）

1. **配列の要素単位編集**（仕様完成・Handoff提示済み・**実装未着手**）
   - 鍵の宣言／参照関係の宣言／順序の宣言＋ add_element / edit_element / retire_element
   - ddd/tech-lead の検証8箇所を反映済み。completionImage の確認は未取得
   - Handoff: `.waffle/documents/handoff/handoff-array-element-editing.json`
2. **操作保証の廃止（v10）**（完了・commit 4307e7f）
3. **古い版を違反として上げる**（仕様・実装とも完了。`aligned` を返す形）
4. **bc-waffle 41件のv10移設**（未着手。v8が31件・v9が10件、`covers` 229件）
5. **サブドメインの配置と切り方の是正**（決定済み・未着手）
   - 配置: `specs/subdomain/sd-*.json` と `specs/bc/bc-waffle/{aggregate,usecase,domain-service}/`、対応は `subdomainRef`
   - tech-lead: **`check_spec_integrity` を先に宣言駆動へ直す**（新配置で静かに空集合を返し、安全網が黙って外れる）。移動は git mv、Waffle に移動コマンドは無い
   - **移動を先にすると、切り方の統合がファイル移動を伴わなくなる**（分類が `subdomainRef` だけで表現されるため）
   - 切り方: 7分割は「意味のない細分化」（core5・generic2にしか落ちず投資判断が変わらない）。統合案は ドリフト検知 / 文書の執筆 / 補完 / 外部への委譲
6. **knowledge の欠落発覚**（ここで脱線）→ 現在地

## Why

サブドメインの切り方を検証する過程で、`subdomain.md` の要約版から「業務領域の境界＝強く関連するユースケースの集まり（図1-3）」が丸ごと落ちていることが判明。advisor はその欠落した knowledge を根拠に判断していた。器が中身を選び、元は「重複となり不要」として削除されていた（commit 1f1a95c、2026-07-10）。

## How to apply

- 書き起こし版は `git show 1f1a95c^` から復元済み。`.waffle/skills/ddd-advisor/references/archive/knowledge-v1-book-transcription/` に19本
- ddd-advisor の `knowledgeRefs` は書き起こし版へ向け直し済み（要約版19本は現在どこからも読まれない）
- 原本PDFは `docs/archives/書籍 2026年6月20日.zip`（342ページ・**スキャン画像でテキスト層なし**）。全文突き合わせは非現実的で、争点が出たページだけ画像で見る運用
- **advisor の判断を再検証する必要がある**。今日の ddd/tech-lead の結論はすべて欠落した knowledge の上で出ている（間違いとは限らないが根拠が不足）
- 既知の穴: `knowledge-cand-*` が `knowledgeRefs` に載っておらず、advisor が読んでいない可能性

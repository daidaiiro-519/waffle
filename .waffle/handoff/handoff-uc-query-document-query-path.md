 

---

# 10操作のJMESPath式操作query_pathへの統合：handoff-uc-query-document-query-path

## 引き継ぎ元spec

uc-query-document

---

## 完成イメージ

---

## 使われ方（実際の呼び出し例）

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| ddd-advisor | get_field/filter_items/get_items_slice等10操作を1つのJMESPath式操作query_pathへ統合する判断の妥当性 | 統合は妥当。理由は、これらの操作名はそもそもユビキタス言語（業務エキスパートの語彙）ではなく「取得手段」を表す実装都合の語彙であり、Waffleの意味の担い手はx-prompt-query由来のprompt（統合後も維持される）だから。 |
| ddd-advisor | 残す3分類（発見系・検索系・変換系）の妥当性 | 「発見系」「検索系」「変換系」の3分類は妥当。根拠は「操作がまたぐ一貫性境界の広さ」であり、検索系=単一document内、発見系=document×schema横断or複数document横断、変換系=参照解決、という境界の広さで分けられている。 |
| ddd-advisor | 3分類内部のグレーゾーン | filter_patternのカスタム関数化は「一語一義」原則的にやや不安（検索系の中に「標準JMESPathモード」と「Waffle固有拡張モード」が隠れる）。「発見系」内部でもget_meta（単一doc）とindex_scan_dir（複数doc横断）は対象範囲が違いすぎ、まとめすぎの可能性がある。いずれも今回のquery_path統合スコープの外側の留意事項として記録する。 |
| ddd-advisor | 複数document横断検索（uc-query-document-collection）をquery_pathの統合対象に含めるべきという提案の再検討 | 再確認の結果、含めないと判定。「実装メカニズムが共通化できること」を直接の根拠に責務境界を統合しようとするのはアンチパターン（design-heuristics.md「大きさから区切られた文脈を決める」の逆転、architecture-patterns.md「技術方式を機械的にコンテキスト全体へ一律適用する」の同型）。分離を維持すべき。ただし内部実装（相対式評価＋ヒット単位の自己記述的レスポンス生成）は共通モジュールとして共有してよい（context-integration.md「モデルの共有」に相当）。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | jmespath依存追加＋カスタム関数拡張という実装方式自体の妥当性 | tech-lead-advisorのバックボーン範囲外（製品選定はADRとして記録すべき事項）。既に.waffle/documents/coding/tech-stack-python-hexagonal.jsonのlibrariesブロックに記録済みであることを確認した。 |
| tech-lead-advisor | 既存operation名の廃止（破壊的変更）への段階的移行パターン | tech-lead-advisorのバックボーン範囲外。正直に「分からない」と回答された。移行パターンの検討は別途必要。 |
| tech-lead-advisor | 検索系・発見系・変換系の3グループ分類のアーキテクチャ上の妥当性 | 「変更を駆動する理由が異なるコードは同じ層にまとめない」（architecture-layer-boundary）の観点からも妥当。検索系=JMESPathライブラリのAPI仕様で変わる、発見系/変換系=Waffle固有ロジックで変わる、という変更理由の違いに対応している。 |
| tech-lead-advisor | 「値を返す全操作にpromptが付く」という絶対制約との整合性 | 重要な指摘。JMESPath式が単一blockKeyに対応しない場合（複数blockTypeを跨ぐ式）に絶対制約が破綻しうる。この指摘を受けて、query_pathは必ずblockKey起点（content[blockKey]の内側だけを対象）で評価する設計に確定した。blockKey省略時は全ブロックへ同じ相対式を個別評価し、ヒットしたブロックだけをブロックごとに分けて返す。doc全体を1つの式で横断することはさせない。 |
| tech-lead-advisor | filter_patternのカスタム関数拡張の技術的実現性 | 技術検証（spike）が先という判定。実際にjmespath.functions.Functions継承でregex_matchカスタム関数を動作確認済み（2026-07-19）。 |

---

## 既知の制約・トレードオフ

- query_pathの式は常に「1ブロックの内側を起点とした相対式」。doc全体や複数blockTypeを跨ぐ式は許可しない
- blockKey指定時の応答形式は既存operationと同じ{"documentId": ..., "prompt": ..., "value": ...}を維持する（既存呼び出し元との互換性）
- blockKey省略時は{"documentId": ..., "results": [{"blockKey": ..., "prompt": ..., "value": ...}, ...]}。ヒットしなかったブロックは省略する
- jmespathの生例外（ParseError等）をそのまま返さず、Waffle独自のエラーコード・メッセージへ変換する
- find_all/resolve_ref/index_scan/index_scan_dir/get_meta/scanの6操作は変更しない
- uc-query-document-collection（grep_documents/filter_documents）はこのタスクのスコープ外、変更しない

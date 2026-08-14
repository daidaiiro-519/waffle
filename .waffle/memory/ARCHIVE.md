# Memory Archive

進行中の作業には要らないが、消していないメモリ。**作業が変わったら [MEMORY.md](MEMORY.md) へ戻す。**
毎セッション読み込まれるのは MEMORY.md だけなので、ここに置いたものは自動では参照されない。

## 図と描画

- [図の関係は記号でなく言葉で表す](feedback_relations_in_words_not_symbols.md) — 凡例が要る記法は持ち込まない
- [図の語彙は3段（主張→比較の方法→描き方）](project_figure_vocabulary_three_tiers.md) — 2段目は既存の確立した枠組みから採る
- [図は本文の幅からはみ出さない](feedback_figure_stays_inside_body_width.md) — 大きくするなら面を縦に積む
- [図の補足は要素を名指しした注釈の表](project_figure_notes_table.md) — 辺の一覧は書き写しで無価値
- [図は描いて画像を読み返してから出す](project_svg_visual_check_loop.md) — resvg-py、フォント未解決で文字が黙って消える罠あり

## 規約・アーキテクチャ

- [規約に分類による場合分けを持ち込まない](feedback_no_conditional_branching_in_architecture_rules.md)
- [ドメイン層のフォルダは種類単位で確定(2026-08-07)](project_domain_folder_unit_is_kind_based.md)
- [名前と実体を一対一にする(2026-08-09)](project_block_key_must_equal_block_type.md)
- [依存検査とプリセット育成の到達点(2026-08-04)](project_dependency_checks_and_preset_growth.md)
- [集約クラス検査の誤検知とトランザクション境界](project_aggregate_drift_and_transaction.md)
- [フックは例外なく仕様で管理する](feedback_hooks_are_spec_managed_without_exception.md)

## 移行・変換の進行状況

- [v10移設の状況とbc-artifact-shareの据え置き](project_v10_migration_status.md)
- [走っている作業の連鎖と現在地(2026-08-11)](project_inflight_work_2026_08_11.md)
- [knowledge 19本のv6変換が完了](project_knowledge_v6_conversion_done.md)
- [変換のたびに書籍の実例を置き換える](feedback_replace_book_examples_in_conversion.md)
- [事業領域／業務領域の語彙を保つ](project_business_domain_vocabulary_kept.md)
- [シナリオとテストの突き合わせ被覆率](scenario-test-pairing-coverage.md)

## 共有・配信

- [artifact-shareは中身を解釈しない共有基盤](project_artifact_share_supersedes_design_share_console.md)
- [design-shareの旧配信機能は復活させない](feedback_design_share_delivery_is_not_restored.md)

## その他の進め方

- [使っていないことは消す理由にならない](feedback_unused_is_not_a_reason_to_remove.md) — 判断基準は「今後そのケースを考慮する必要があるか」
- [依頼された軸から外れない](feedback_stay_on_the_asked_axis.md)
- [renderは確認用の読み取りではない](feedback_render_is_not_a_read_operation.md)
- [選択が届かなかったら確認する](feedback_confirm_unregistered_selection.md)

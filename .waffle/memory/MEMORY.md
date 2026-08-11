# Memory Index

ツールを問わず共有されるメモリ索引。記録・更新は`memory-cultivator` Skillを通じて行う。既存の`.claude/projects/.../memory/`（Claude Code専用の自動メモリ機構）とは並行運用し、新規メモリのみここへ書く（詳細は`docs/brainstorm/brainstorm-waffle-memory-mechanism.md`）。

- [確認せず手が動く方へ進む癖](skip-confirmation-before-acting.md) — 工程の次段階・schemaのx-prompt・実物を、記憶で判断せず必ず開いて確かめる
- [シナリオとテストの突き合わせ被覆率](scenario-test-pairing-coverage.md) — 突き合わせの3つ組（層・spec・シナリオ）の設計結論と、相手のいない176件の内訳
- [x-promptは根幹であって付随物ではない](feedback_x_prompt_is_the_core_not_metadata.md) — writeとqueryが同じ欄で矛盾/enum変更に未追随、構造変更時は必ず対で見直す
- [使っていないことは消す理由にならない](feedback_unused_is_not_a_reason_to_remove.md) — 判断基準は「今後そのケースを考慮する必要があるか」。同型の誤りを繰り返している
- [依存検査とプリセット育成の到達点(2026-08-04)](project_dependency_checks_and_preset_growth.md) — 層/循環の検査・規約19→15・update-coding-preset・MCP有効化まで完了、残る論点6件
- [artifact-shareは中身を解釈しない共有基盤、design-shareはモック作成の補助へ一般化(2026-08-05)](project_artifact_share_supersedes_design_share_console.md) — コメント同期も判定もartifact-share側に既存。design-shareは配信を一切持たず、配信はartifact-shareのMCP経由
- [規約は1ブロックだけ読んで判断しない](feedback_read_all_standards_not_one_block.md) — test-standardに専用のdocstring規約がある等。同じ形の誤りを1日に3回やった
- [依頼された軸から外れない](feedback_stay_on_the_asked_axis.md) — docstringは「形式に沿っているか」。有無・可視性・dunderへ広げない。軸ごとに件数を測れば本題が分かる
- [規約に分類による場合分けを持ち込まない](feedback_no_conditional_branching_in_architecture_rules.md) — フォルダはconceptPlacementが直接1つ宣言する。1文書が複数分類を束ねるので導出規則は文書内で分岐を生む
- [ドメイン層のフォルダは種類単位で確定(2026-08-07)](project_domain_folder_unit_is_kind_based.md) — 集約単位は共有される値オブジェクト(ViewToken 3件×2集約)で破綻。未了の実害4件も併記
- [renderは確認用の読み取りではない](feedback_render_is_not_a_read_operation.md) — 配置先の真実源は.waffle/config.json。orchestratorだけ定数パスで、雛形renderがCLAUDE.md/AGENTS.mdを壊した実例あり
- [仕様と実装の抽象境界の結論(2026-08-09)](project_ddd_abstraction_boundary_conclusions.md) — 原則/Waffleの設計判断/未採用の提案を三分割。ポートを仕様に書く案は取り下げ、根拠つき
- [仕様の語彙にパターン名を入れない](feedback_no_pattern_names_in_spec_vocabulary.md) — port/Primary/Secondaryは様式の語彙。使えるのは規約から下だけ。同日3回持ち込んだ
- [選択肢を並べて「どうしますか」と聞かない](feedback_lead_with_position_before_asking.md) — 見解・推奨・理由・衝突を先に出し、問いは自分の案への可否確認の形にする
- [名前と実体を一対一にする(2026-08-09)](project_block_key_must_equal_block_type.md) — 鍵(blockKey⇄blockType)と形(同じblockTypeが違う構造)の両方。schemaの読み書き手順つき
- [design-shareの旧配信機能は復活させない](feedback_design_share_delivery_is_not_restored.md) — 「一時的に失われる」と書くと移植TODOとして読まれる。判断が済んでいる形で書く
- [実例の件数で能力の要否を決めない](feedback_evidence_based_scope_is_not_for_capability_decisions.md) — 抽象化のタイミングの基準であって、作るか作らないかの判断には使えない。3度目の再発
- [v10移設の状況とbc-artifact-shareの据え置き](project_v10_migration_status.md) — 操作保証を廃止、bc-waffleは41件が未追従(v8:31/v9:10、covers 229件)、artifact-shareは意図的にv8
- [走っている作業の連鎖と現在地(2026-08-11)](project_inflight_work_2026_08_11.md) — 配列要素編集→v10→版ドリフト→41件移設→サブドメイン是正→knowledge欠落、で脱線中
- [集約クラス検査の誤検知とトランザクション境界](project_aggregate_drift_and_transaction.md) — 中間項が機械可読でないのが原因、knowledge片付け後に着手
- [変換のたびに書籍の実例を置き換える](feedback_replace_book_examples_in_conversion.md) — 構造は保ち題材だけ差し替え、grepで0件確認。1本目の訂正を規則にせず2度指摘された

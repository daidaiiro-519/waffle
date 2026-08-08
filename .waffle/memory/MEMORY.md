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
- [design-shareの旧配信機能は復活させない](feedback_design_share_delivery_is_not_restored.md) — 「一時的に失われる」と書くと移植TODOとして読まれる。判断が済んでいる形で書く

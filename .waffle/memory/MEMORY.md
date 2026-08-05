# Memory Index

ツールを問わず共有されるメモリ索引。記録・更新は`memory-cultivator` Skillを通じて行う。既存の`.claude/projects/.../memory/`（Claude Code専用の自動メモリ機構）とは並行運用し、新規メモリのみここへ書く（詳細は`docs/brainstorm/brainstorm-waffle-memory-mechanism.md`）。

- [確認せず手が動く方へ進む癖](skip-confirmation-before-acting.md) — 工程の次段階・schemaのx-prompt・実物を、記憶で判断せず必ず開いて確かめる
- [シナリオとテストの突き合わせ被覆率](scenario-test-pairing-coverage.md) — 突き合わせの3つ組（層・spec・シナリオ）の設計結論と、相手のいない176件の内訳
- [x-promptは根幹であって付随物ではない](feedback_x_prompt_is_the_core_not_metadata.md) — writeとqueryが同じ欄で矛盾/enum変更に未追随、構造変更時は必ず対で見直す
- [使っていないことは消す理由にならない](feedback_unused_is_not_a_reason_to_remove.md) — 判断基準は「今後そのケースを考慮する必要があるか」。同型の誤りを繰り返している
- [依存検査とプリセット育成の到達点(2026-08-04)](project_dependency_checks_and_preset_growth.md) — 層/循環の検査・規約19→15・update-coding-preset・MCP有効化まで完了、残る論点6件
- [artifact-shareは中身を解釈しない共有基盤、design-shareはモック作成の補助へ一般化(2026-08-05)](project_artifact_share_supersedes_design_share_console.md) — コメント同期も判定もartifact-share側に既存。design-shareは配信を一切持たず、配信はartifact-shareのMCP経由
- [design-shareの旧配信機能は復活させない](feedback_design_share_delivery_is_not_restored.md) — 「一時的に失われる」と書くと移植TODOとして読まれる。判断が済んでいる形で書く

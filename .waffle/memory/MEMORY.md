# Memory Index

ツールを問わず共有されるメモリ索引。記録・更新は`memory-cultivator` Skillを通じて行う。既存の`.claude/projects/.../memory/`（Claude Code専用の自動メモリ機構）とは並行運用し、新規メモリのみここへ書く（詳細は`docs/brainstorm/brainstorm-waffle-memory-mechanism.md`）。

- [確認せず手が動く方へ進む癖](skip-confirmation-before-acting.md) — 工程の次段階・schemaのx-prompt・実物を、記憶で判断せず必ず開いて確かめる
- [シナリオとテストの突き合わせ被覆率](scenario-test-pairing-coverage.md) — 突き合わせの3つ組（層・spec・シナリオ）の設計結論と、相手のいない176件の内訳
- [x-promptは根幹であって付随物ではない](feedback_x_prompt_is_the_core_not_metadata.md) — writeとqueryが同じ欄で矛盾/enum変更に未追随、構造変更時は必ず対で見直す

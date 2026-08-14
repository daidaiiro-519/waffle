# Memory Index

ツールを問わず共有されるメモリ索引。記録・更新は`memory-cultivator` Skillを通じて行う。

**いまの索引は、進行中の作業（仕様と実装の抽象境界を決定として記録する）に要るものだけを載せている。** それ以外は [ARCHIVE.md](ARCHIVE.md) にあり、ファイルは消していない。作業が変わったら索引を組み替える。

## 進め方

- [選択肢を並べて「どうしますか」と聞かない](feedback_lead_with_position_before_asking.md) — 見解・推奨・理由・衝突を先に出し、問いは自分の案への可否確認の形にする
- [確認せず手が動く方へ進む癖](skip-confirmation-before-acting.md) — 工程の次段階・schemaのx-prompt・実物を、記憶で判断せず必ず開いて確かめる
- [規約は1ブロックだけ読んで判断しない](feedback_read_all_standards_not_one_block.md) — 定義の本文・判断の木・表を全部当たってから断じる。同じ形の誤りを繰り返している
- [実例の件数で能力の要否を決めない](feedback_evidence_based_scope_is_not_for_capability_decisions.md) — 抽象化のタイミングの基準であって、構造の妥当性の検査には使えない

## 主題（仕様と実装の抽象境界）

- [仕様と実装の抽象境界の結論(2026-08-09)](project_ddd_abstraction_boundary_conclusions.md) — この作業の前回の到達点。原則／Waffleの設計判断／未採用の提案／取り下げの四分割
- [抽象は情報の削減ではない](feedback_abstraction_is_not_reduction.md) — 要素は残し、共通概念で束ねる。具体を復元するのに要る特徴を落とさない
- [仕様の語彙にパターン名を入れない](feedback_no_pattern_names_in_spec_vocabulary.md) — port/Primary/Secondaryは様式の語彙。使えるのは規約から下だけ
- [x-promptは根幹であって付随物ではない](feedback_x_prompt_is_the_core_not_metadata.md) — writeとqueryが同じ欄で矛盾しうる。構造変更時は必ず対で見直す
- [schemaの指示でknowledgeを広げない](feedback_schema_prompts_must_not_widen_knowledge.md) — 導出の向きはknowledge→x-prompt。ただし広いと断じる前に定義を全文読む

## 決定の記録の形

- [ADRは1決定。粒度と決定の抽象化](feedback_adr_granularity_and_decision_abstraction.md) — 自分の理由・軸・答えないことを要するなら独立。数が増えすぎないよう決定自体を上げる
- [理由は連鎖で書き、前提に崩れる条件を添える](feedback_reason_is_a_chain_with_weak_points.md) — 測った／確かめていないを分け、末尾に反証。空なら「探したが見つからない」と書く
- [補助の情報は読み手が要る時点で前後を決める](feedback_information_before_or_after_by_reading_need.md) — 読むために要るなら前、疑うときに要るなら後ろ。中身の形では決めない

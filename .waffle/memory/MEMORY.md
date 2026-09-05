# Memory Index

ツールを問わず共有されるメモリ索引。記録・更新は`memory-cultivator` Skillを通じて行う。

**いまの索引は、進行中の作業（仕様と実装の抽象境界を決定として記録する）に要るものだけを載せている。** それ以外は [ARCHIVE.md](ARCHIVE.md) にあり、ファイルは消していない。作業が変わったら索引を組み替える。

## 進め方

- [main で直接コミットする](feedback_commit_on_main_directly.md) — 使うのは1人。ブランチは切らない。ただし1回のコミットに全部を丸めない
- [選択肢を並べて「どうしますか」と聞かない](feedback_lead_with_position_before_asking.md) — 見解・推奨・理由・衝突を先に出し、問いは自分の案への可否確認の形にする
- [確認せず手が動く方へ進む癖](skip-confirmation-before-acting.md) — 工程の次段階・schemaのx-prompt・実物を、記憶で判断せず必ず開いて確かめる
- [消えたと判断する前に会話の記録を探す](feedback_lost_work_lives_in_the_transcript.md) — Writeの中身がそのまま残っている。git と作業領域だけ見て断じない
- [検査の合否だけで「確認した」と言わない](feedback_look_at_the_render_not_only_the_checks.md) — **いま触った図だけ**を1枚見る。回帰の目視・ページ全体の撮影・明暗2通りは要らない（実測：458回の読み返しで666kトークン。生成そのものは0）。機械の検査は維持する
- [HTMLページを画像にする手段＝playwright](project_playwright_page_screenshot.md) — tools/shoot.py。`LD_LIBRARY_PATH=$HOME/.cache/waffle-shoot-libs` が必須（libasound欠け）
- [規約は1ブロックだけ読んで判断しない](feedback_read_all_standards_not_one_block.md) — 定義の本文・判断の木・表を全部当たってから断じる。同じ形の誤りを繰り返している
- [schema を変えるのは実装である](feedback_schema_change_is_implementation.md) — 決定→仕様→実装。仕様を飛ばすと説明の無い構造が増える
- [既存へ肉付けせず、あるべき形へ直す](feedback_correct_toward_the_right_form_not_the_existing_one.md) — 前提が変わった構造に規則を足さない。AIで直す手間は安くなった
- [再定義では既存を根拠にしない](feedback_redefinition_does_not_reason_from_the_existing.md) — 実測は数えるためであって、あるべき形を決める根拠にはしない。2026-08-18に3回差し戻された

## 主題（仕様と実装の抽象境界）

- [いまの現在地：Waffle 自身の knowledge を立てる段](project_waffle_own_knowledge_stage.md) — **ここから再開する。**「段1・段2 でやること」の節に、未決・未承認・順番を1か所へ集約（2026-08-29）

- [schema観の三層と、単位は読み手に従属すること(2026-09-05)](project_schema_conception_reader_dependent_units.md) — abstract/concrete/文書エンティティのメタ三層。人＝文書単位／AI＝節単位。論点3は**節に不変の印を持たせる**で決着（2026-09-05）。**再開点は論点6（規則の置き場所）**
- [仕様と実装の抽象境界の結論(2026-08-09)](project_ddd_abstraction_boundary_conclusions.md) — この作業の前回の到達点。原則／Waffleの設計判断／未採用の提案／取り下げの四分割
- [抽象は情報の削減ではない](feedback_abstraction_is_not_reduction.md) — 要素は残し、共通概念で束ねる。具体を復元するのに要る特徴を落とさない
- [knowledgeが空けている場所を先に見つける](feedback_find_the_gap_knowledge_left_open.md) — 既にある部分を決め直さない。留保事項は「どこが決定に開かれているか」の目印
- [抽象の記録に具体の識別子を並べない](feedback_no_concrete_identifiers_in_abstraction_records.md) — 主語は測り方・範囲・関係に保つ。実例は折りたたみの裏付けへ
- [仕様の語彙にパターン名を入れない](feedback_no_pattern_names_in_spec_vocabulary.md) — port/Primary/Secondaryは様式の語彙。使えるのは規約から下だけ
- [x-promptは根幹であって付随物ではない](feedback_x_prompt_is_the_core_not_metadata.md) — writeとqueryが同じ欄で矛盾しうる。構造変更時は必ず対で見直す
- [schemaの指示でknowledgeを広げない](feedback_schema_prompts_must_not_widen_knowledge.md) — 導出の向きはknowledge→x-prompt。ただし広いと断じる前に定義を全文読む

## 主題（svg_engine PoC ── design-svg Skillの事業領域）

- [svg_engineはdesign-svgの事業領域、Waffleは利用側](project_svg_engine_visual_check_hook_pending.md) — 16の主張という記法も含めてdesign-svgが所有。Waffleは変換器越しに使う想定（今回は無し）。design-svgのSKILL.mdの除外規定が現状と矛盾したまま残っている。描画機械チェックのhook化・所有権整理は他のschema再定義が一段落してから
- [辺の着き先を、インクから選ぶ形へ作り替えた(2026-08-23)](project_svg_engine_attachment_redesign.md) — 索引 a37fc94b。輪郭の申告をやめ、検査に `check_attachment` を足した。**決定4本すべて承認済み。**開いたまま2件（湾の凹んだ側＝現状維持／群を指す辺＝宣言手段が無い）
- [描画エンジンの規律を決めた(2026-08-29)](project_svg_engine_architecture_discipline.md) — **ヘキサゴナル/クリーンアーキ/オニオンは採らない**（中心も外周も空。advisor2体と独立に一致）。厳格な層状＋パイプとフィルタ＋関数核の3規約と、構造で縛れない分の件数の天井。**承認済み・実装は未着手**（順序: 静的検査器 → 規約1と3 → 規約2 → 天井）
- [Waffle変換器＋段1/段2再開のTODO棚卸し(2026-08-22)](project_svg_stage12_todo_artifact.md) — アーティファクトへのポインタ。作業再開時にまずここを開く

## 決定の記録の形

- [ADRは1決定。粒度と決定の抽象化](feedback_adr_granularity_and_decision_abstraction.md) — 自分の理由・軸・答えないことを要するなら独立。数が増えすぎないよう決定自体を上げる
- [主語と目的語を省いて短くしない](feedback_state_who_does_what_to_what.md) — 誰が・何を・何に対してを残す。語彙より先に文法の欠けで詰まる
- [どの欄も結論の一文で始める](feedback_every_column_leads_with_its_conclusion.md) — 面や列の見出しも同じ（変更前 ── …）。連鎖の末尾に結論があることは一文の代わりにならない
- [理由は連鎖で書き、前提に崩れる条件を添える](feedback_reason_is_a_chain_with_weak_points.md) — 測った／確かめていないを分け、末尾に反証。空なら「探したが見つからない」と書く
- [補助の情報は読み手が要る時点で前後を決める](feedback_information_before_or_after_by_reading_need.md) — 読むために要るなら前、疑うときに要るなら後ろ。中身の形では決めない

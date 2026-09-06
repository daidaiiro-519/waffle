# いまどこにいるか

**ここは、セッションをまたいで引き継ぐ「現在地」だけを置く。**
守らなければいけないことは knowledge か Skill が持つ ── ここには写さない。
作業が終わった項目は消す。**過去の決定を残さない**（当てにならなくなり、次の思考のノイズになる）。

更新日: 2026-09-05

## 走っている作業

- **社内AI人材育成ワークショップ** ── [開催条件と目的](project-ai-workshop.md)。部長向け17枚をレビュー中。作者の暗黙知に依存しない他者利用、初心者向け設問、支援・発表・評価の図解を本編へ反映。設問の正本は `docs/workshops/ai-workshop/survey-and-evaluation.md`。日程・尺度の確定と受講者向け教材はこれから。

- **schema 観の三層（段1・段2 の再定義）** ── 盤面 `docs/adr/brainstorm-schema-conception-board.html`
  （Artifact: `https://claude.ai/code/artifact/b85a142f-d6b5-4964-844c-0f7c64383882`）。
  **12論点すべて決着（2026-09-06）。** 三層／単位は読み手に従属／型は横に増える／節に印／
  規則は述語＋検査の名前（名簿は2段）／型は意味・形は射影（既定＋差分）／2状態で承認したら畳む／
  承認は意思決定の境目でだけ／指示は x- に構造で持ち渡すとき合成／版は Waffle の版に従い破壊は認める／
  変更の記録は abstract の契約・ADR は concrete（3種）／引くのは述語で読み方を必ず添える。
  **論点16 決着（2026-09-06）**── CodingSchema の種は CodingSkills の雛形の単位15にし、
  **古い4種（architecture/coding-standard/tech-stack/test-standard）は捨てる**。層は軸から導出、
  種別は欄。既存の coding 系 document 12本は再定義の一部として作り直す。
  **論点15 も決着**── spec の軸は 業務（主題）・接点・基盤で、層はどれも業務を含む
  （業務／業務×接点／業務×基盤）。業務を含まない層は spec ではなく規約。UI/API/CLI/MCP は接点の値。
  原典は 業務＝ddd-advisor の knowledge、接点＝Fowler の層分け＋Cockburn、基盤＝Platform Engineering と SLI/SLO。
  **残るは論点14（型を立てる基準）だけ。**


## 承認待ち

- **書き方の規約を、メモリから Skill へ移す提案** ── `docs/adr/rules-move-from-memory-to-skills.html`。
  正本へはまだ当てていない。
- **`spec-correspondence` から移した3つのSkill**（change-record・writing-guard・source-fidelity）は、
  **こちらで育てて原本へ反映する**と決まった（2026-09-06）。
  `source-fidelity` と `change-record` は両リポジトリへ当ててコミット済み。
  **`writing-guard` は waffle から消し、`doc-writing-skills` へ置き換えた**（2026-09-06）──
  5つの原典から10概念を抜き出し、規則と判定へ降ろした。ゲートは2つ（機械が決めるもの・書き手が言うもの）。
  **`spec-correspondence` 側の `writing-guard` は残している**——統制実験の道具として20以上の文書が参照しているため。

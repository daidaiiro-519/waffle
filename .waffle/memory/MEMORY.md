# いまどこにいるか

**ここは、セッションをまたいで引き継ぐ「現在地」だけを置く。**
守らなければいけないことは knowledge か Skill が持つ ── ここには写さない。
作業が終わった項目は消す。**過去の決定を残さない**（当てにならなくなり、次の思考のノイズになる）。

更新日: 2026-09-05

## 走っている作業

- **社内AI人材育成ワークショップ** ── [開催条件と目的](project-ai-workshop.md)。部長向け資料をレビュー中。表紙を加えた15枚で、冒頭に抽象と具体の往復を置く。開催条件の具体化と受講者向け教材はこれから。資料は `docs/workshops/ai-workshop/`。

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
  `source-fidelity` は 2.0.0 まで進めて両リポジトリへ当てた（**まだコミットしていない**）──
  主張と引用の照合（Step 4）・外を指す参照の除去・当て方の作り直し（`--as` 3種）・振る舞いテスト33件。
  `tabs.py` の遅れも取り込み済み。**スクリプトは3つとも `scripts/` へ移した**（`references/` は文書とデータだけ）。

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
  **次は、この12を段1・段2 の spec へ落とすこと。**盤面の「まとめ」に保留9件も並べてある。


## 承認待ち

- **書き方の規約を、メモリから Skill へ移す提案** ── `docs/adr/rules-move-from-memory-to-skills.html`。
  正本へはまだ当てていない。
- **`spec-correspondence` から移した3つのSkill**（change-record・writing-guard・source-fidelity）は、
  原本と同一のまま置いてある。**こちらで育てるのか、原本に追随するのかは未決。**
  `change-record/references/tabs.py` は複製後に原本へ現れたもので、まだ取り込んでいない。

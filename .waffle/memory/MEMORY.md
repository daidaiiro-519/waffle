# いまどこにいるか

**ここは、セッションをまたいで引き継ぐ「現在地」だけを置く。**
守らなければいけないことは knowledge か Skill が持つ ── ここには写さない。
作業が終わった項目は消す。**過去の決定を残さない**（当てにならなくなり、次の思考のノイズになる）。

更新日: 2026-09-05

## 走っている作業

- **schema 観の三層（段1・段2 の再定義）** ── 盤面 `docs/adr/brainstorm-schema-conception-board.html`。
  論点1・2・5・3 が決着し、**再開点は論点6（規則を、コマンドで持つか宣言で持つか）**。
  論点7（書く単位と承認する単位のずれ）は論点6 のあと。
- **CodingSkills（規約に従って書く汎用Skill）** ── 盤面 `docs/adr/brainstorm-coding-skills.html`
  （Artifact: `https://claude.ai/code/artifact/f59a20eb-4dfa-45d3-bdbf-21d8abbe060c`）。
  **8論点すべて決着（2026-09-05）。次は、制約1件が持つ欄の設計。**
  Waffle を前提にしない形で組み、段1・段2 が決まったらそちらへ寄せる。

## 承認待ち

- **書き方の規約を、メモリから Skill へ移す提案** ── `docs/adr/rules-move-from-memory-to-skills.html`。
  正本へはまだ当てていない。
- **`spec-correspondence` から移した3つのSkill**（change-record・writing-guard・source-fidelity）は、
  原本と同一のまま置いてある。**こちらで育てるのか、原本に追随するのかは未決。**
  `change-record/references/tabs.py` は複製後に原本へ現れたもので、まだ取り込んでいない。

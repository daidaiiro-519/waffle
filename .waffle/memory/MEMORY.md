# いまどこにいるか

**ここは、セッションをまたいで引き継ぐ「現在地」だけを置く。**
守らなければいけないことは knowledge か Skill が持つ ── ここには写さない。
作業が終わった項目は消す。**過去の決定を残さない**（当てにならなくなり、次の思考のノイズになる）。

更新日: 2026-09-05

## 走っている作業

- **社内AI人材育成ワークショップ** ── [開催条件と目的](project-ai-workshop.md)。部長向け資料をレビュー中。表紙を加えた15枚で、冒頭に抽象と具体の往復を置く。開催条件の具体化と受講者向け教材はこれから。資料は `docs/workshops/ai-workshop/`。

- **schema 観の三層（段1・段2 の再定義）** ── 盤面 `docs/adr/brainstorm-schema-conception-board.html`
  （Artifact: `https://claude.ai/code/artifact/b85a142f-d6b5-4964-844c-0f7c64383882`）。
  論点1・2・5・3・6・8 が決着（2026-09-06）。**残るは論点7（書く単位と承認の単位のずれ）1つだけ**。
  論点8 で「型は意味・形は射影／既定＋差分／組は並べ方だけ」まで決まっている。
- **CodingSkills（規約に従って書く汎用Skill）** ── `.waffle/skills/coding-skills/`（第1版・2026-09-05）。
  盤面 `docs/adr/brainstorm-coding-skills.html`、面 `docs/adr/coding-skills-templates.html`
  （Artifact: `https://claude.ai/code/artifact/24732a71-b357-41a1-8f53-fbb87417f92d`）。
  **雛形15本・規約37本・原典41本。形の検査はすべて通っている。**
  **残る未知は「集めた規約だけで実際に書けるか」1つで、別リポジトリでの効果測定で測る。**
  段1・段2 が決まったら schema の形へ寄せる。

## 承認待ち

- **書き方の規約を、メモリから Skill へ移す提案** ── `docs/adr/rules-move-from-memory-to-skills.html`。
  正本へはまだ当てていない。
- **`spec-correspondence` から移した3つのSkill**（change-record・writing-guard・source-fidelity）は、
  原本と同一のまま置いてある。**こちらで育てるのか、原本に追随するのかは未決。**
  `change-record/references/tabs.py` は複製後に原本へ現れたもので、まだ取り込んでいない。

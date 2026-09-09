# いまどこにいるか

**ここは、セッションをまたいで引き継ぐ「現在地」だけを置く。**
守らなければいけないことは knowledge か Skill が持つ ── ここには写さない。
作業が終わった項目は消す。**過去の決定を残さない**（当てにならなくなり、次の思考のノイズになる）。

更新日: 2026-09-09

## 走っている作業

- **社内AI人材育成ワークショップ** ── [開催条件と目的](project-ai-workshop.md)。部長向け17枚をレビュー中。作者の暗黙知に依存しない他者利用、初心者向け設問、支援・発表・評価の図解を本編へ反映。設問の正本は `docs/workshops/ai-workshop/survey-and-evaluation.md`。日程・尺度の確定と受講者向け教材はこれから。

- **schema 観の三層（段1・段2 の再定義）** ── 盤面 `docs/adr/brainstorm-schema-conception-board.html`
  （Artifact: `https://claude.ai/code/artifact/b85a142f-d6b5-4964-844c-0f7c64383882`）。
  索引 `docs/adr/schema-conception-index.html`（Artifact: `https://claude.ai/code/artifact/e057e7a4-7555-48ad-9606-236e3e5442cc`）── **次のセッションはここから入る**。
  **20論点のうち15が決着。残る未決は5つだけ**（2026-09-09）。

  | # | 問い | 推し |
  |---|---|---|
  | 14 | 何を1つの型として立てるか | **D**：型は軸の集合で決まる。層は軸から導出、種はその層で決まることの単位 |
  | 18 | Hook や Skill の中の処理をどこに紐づけるか | **B**：能力は業務の層／差し出し方は業務×接点／script は呼ぶだけ |
  | 17 | ADR 以外を schema で持つか | **D**：ADR・knowledge・skill・agent は文書、template は型にしない、hook は中身で仕分ける |
  | 19 | 層ごとに何を1つの文書の単位にするか | **B**：業務8＋接点2＋基盤1 |
  | 20 | どういうフォルダの形で置くか | **B**：業務でフォルダを切る |

  **順番は 14 → 18 → 17 → 19 → 20。**17 は 14（どう切るか）と 18（いつ起きるか）に依存する。
  19・20 は 14 が決まれば従属する。

  **語の定義（14 の前提）** ── 型＝concrete schema 1本、種＝その中の discriminator、
  軸＝何に依存して変わるかの1本（判定は「1つ固定して他が動くか」）。
  値が増えるだけなら型は増えない（論点5）。

  **論点17 は一度割り直した（2026-09-09）** ── 崩れうるところ4つのうち、
  「いつ走らせるか」は論点18、「どう切るか」は論点14 の持ち物だった。
  **「禁止は規則へ」は文言の誤り**で、禁止は〈規則＝述語（何が違反か）〉と
  〈接点の扱い（止める・報告する・並べる）〉の2つに割れる ── 規則に止める力を持たせると
  abstract の動詞が増え、論点5 に反する。**17 が答えるのは「schema で持つか」だけ**。

  **決着済み15の要点**：三層／単位は読み手に従属／型は横に増える／節に印／
  規則は述語＋検査の名前（名簿は2段）／型は意味・形は射影（既定＋差分）／2状態で承認したら畳む／
  承認は意思決定の境目でだけ／指示は x- に構造で持ち渡すとき合成／版は Waffle の版に従い破壊は認める／
  変更の記録は abstract の契約・ADR は concrete（3種）／引くのは述語で読み方を必ず添える／
  **論点16**＝CodingSchema の種は雛形の単位15（古い4種は捨てる。既存 coding 系 document 12本は作り直す）／
  **論点15**＝spec の軸は 業務（主題）・接点・基盤で、層はどれも業務を含む。
  業務を含まない層は spec ではなく規約。UI/API/CLI/MCP は接点の値。

  **描かれた姿（決まったことだけから組んだ、欄は仮置き）**
  ── 仕様の文書 `docs/adr/spec-doc-preview.html`
  （`https://claude.ai/code/artifact/f8340f9a-85f8-4612-8db8-1ea503ad722d`）／
  関係と文脈の地図 `docs/adr/relationship-map-preview.html`
  （`https://claude.ai/code/artifact/eaf1b27c-9027-4aa5-aade-57fcd55baf0e`）。
  **関係は1件ずつ文書になり、地図は保存せず描く**（頂点＝文脈、線は文書どうしの参照から導き、
  ラベルは関係の宣言から取る）。宣言と参照が別入力なので、両者のずれが違反として出る。

- **進め方を「承認だけで進む」形へ変える（合意前）** ──
  案を並べて選ばせるのをやめ、答えを1つ出して諾否を問う形にする。
  経緯と適用の仕方は [feedback-approval-not-selection.md](feedback-approval-not-selection.md)。
  体験用の画面 `docs/adr/approval-only-simulator.html`
  （`https://claude.ai/code/artifact/d304e1c8-be09-4926-95ab-c1a37e7da06e`）と、
  回答の受け渡しの構成 `docs/adr/answer-pipeline.html`
  （`https://claude.ai/code/artifact/8d9e2335-5898-4aeb-a6b1-121dbb49ab48`）まで提示済み。
  **作ってよいかの承認は、まだもらっていない**（増える物は serve.py ・ フック1本 ・ JSON Schema 1本）。
  未決5論点は、合意が取れ次第この形で出し直す。

- **CodingSkills の軸の記述を直す（未着手）** ── `.waffle/skills/coding-skills/`。
  SKILL.md と glossary.md が**軸を4つ（言語・アーキ・用途・実行環境）**と書いているが、
  **実行環境だけを条件にした層は0本**で、`runtime` は用途が決めている（backend-api→resident、
  hook→per-invocation、mcp-server→resident）。**軸は3本**が正しく、実行環境は規約が宣言する欄。
  論点14 の基準を当てて見つけた食い違いで、**直すのは CodingSkills 側だけ。盤面の決まりは変わらない。**


## 承認待ち

- **書き方の規約を、メモリから Skill へ移す提案** ── `docs/adr/rules-move-from-memory-to-skills.html`。
  正本へはまだ当てていない。
- **`spec-correspondence` から移した3つのSkill**（change-record・writing-guard・source-fidelity）は、
  **こちらで育てて原本へ反映する**と決まった（2026-09-06）。
  `source-fidelity` と `change-record` は両リポジトリへ当ててコミット済み。
  **`writing-guard` は waffle から消し、`doc-writing-skills` へ置き換えた**（2026-09-06）──
  5つの原典から10概念を抜き出し、規則と判定へ降ろした。ゲートは2つ（機械が決めるもの・書き手が言うもの）。
  **`spec-correspondence` 側の `writing-guard` は残している**——統制実験の道具として20以上の文書が参照しているため。

---
name: feedback_render_is_not_a_read_operation
description: waffle renderは確認用の読み取りではなく、文書側の値を持たない配置先へ書き込む破壊的操作。中身を見たいだけならqueryを使う
metadata:
  type: feedback
---

`waffle render` は「成果物を確定させる」書き込み操作であり、確認目的で気軽に実行してよいコマンドではない。

**deploy先の真実源は `.waffle/config.json` の `toolMappings`**（Agent/Skill/Knowledge/Coding の4型。schemaの `x-render-target.deploy` は読まれない。`render_document.py:150-159`）。このうち `Agent` の `agentKind=orchestrator` だけが `CLAUDE.md` / `AGENTS.md` という**変数を1つも含まない定数**で、他は全て `{documentId}` 等を含む。

**実際に起きたこと（2026-08-08）**: 汎用テンプレートである `generic-role-skill-orchestrator.json`（tags: `kind:template`, `waffle-independent`）を「レンダリングできるか確かめる」目的で `waffle render` したところ、リポジトリ自身の2本のシンボリックリンクがプレースホルダーだらけの雛形を指すよう張り替えられた。復旧は `git restore CLAUDE.md AGENTS.md`。

**Why:** 配置先が定数なので、同じ種別の文書が複数あれば必ず1点を奪い合う。後にrenderした方が無条件に勝つ（last-write-wins）ため、これは操作ミスではなく構造上の必然で、同じ操作をすれば必ず再現する。documentのtagsやstatusは配置の有無に影響しない。

**How to apply:**
- documentの中身を見たいだけなら `waffle query --operation index_scan` → `query_path --expression "@"` を使う。renderは使わない
- renderを実行する前に、そのschemaのdeploy先が何かを確認する。`waffle render` の戻り値 `deployed` に出るファイルは、実行前に把握できていなければならない
- `waffle render-blank-template` も同様に、`.waffle/templates/blank/` 配下へファイルを書き出す副作用がある（純粋な標準出力コマンドではない）

関連: [[skip-confirmation-before-acting]]（記憶で判断せず実物を確かめる癖）、[[feedback_x_prompt_is_the_core_not_metadata]]

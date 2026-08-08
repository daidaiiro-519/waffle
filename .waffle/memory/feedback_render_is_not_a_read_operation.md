---
name: feedback_render_is_not_a_read_operation
description: waffle renderは確認用の読み取りではなく、schema固定のdeploy先へ書き込む破壊的操作。中身を見たいだけならqueryを使う
metadata:
  type: feedback
---

`waffle render` は「成果物を確定させる」書き込み操作であり、確認目的で気軽に実行してよいコマンドではない。deploy先は**document側ではなくschema側**（`x-render-target`）に固定されているため、documentを取り違えると意図しないファイルを上書きする。

**実際に起きたこと（2026-08-08）**: 汎用テンプレートである `generic-role-skill-orchestrator.json`（tags: `kind:template`, `waffle-independent`）を「レンダリングできるか確かめる」目的で `waffle render` したところ、AgentSchemaのdeploy先が `CLAUDE.md` / `AGENTS.md` 固定であるため、リポジトリ自身の2本のシンボリックリンクがプレースホルダーだらけの雛形を指すよう張り替えられた。復旧は `git restore CLAUDE.md AGENTS.md`。

**Why:** deploy先がschema単位の定数なので、同じschemaを使う限り「これは雛形だから配置されないはず」という期待は成り立たない。documentのtagsやstatusはdeployの有無に影響しない。

**How to apply:**
- documentの中身を見たいだけなら `waffle query --operation index_scan` → `query_path --expression "@"` を使う。renderは使わない
- renderを実行する前に、そのschemaのdeploy先が何かを確認する。`waffle render` の戻り値 `deployed` に出るファイルは、実行前に把握できていなければならない
- `waffle render-blank-template` も同様に、`.waffle/templates/blank/` 配下へファイルを書き出す副作用がある（純粋な標準出力コマンドではない）

関連: [[skip-confirmation-before-acting]]（記憶で判断せず実物を確かめる癖）、[[feedback_x_prompt_is_the_core_not_metadata]]

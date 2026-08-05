---
name: project-artifact-share-supersedes-design-share-console
description: artifact-shareはdesign-shareから派生した「中身を解釈しない共有基盤」で、design-shareはUIデザインモック作成を補助するだけのSkillへ一般化される。コメントレビューも同期も既にartifact-share側にある
metadata:
  type: project
---

2026-08-05 にユーザーとの対話で確定した整理。**どこにも記録されていなかった**
（artifact-share の SKILL.md にも spec にも design-share への言及なし）。

**結論**

- **artifact-share** = 中身を解釈しない共有基盤。生成元を問わない
- **design-share** = UIデザインモック作成を補助するだけの Skill。配ることを一切知らない

design-share の localhost 管理コンソール（`scripts/console_server.py`、1087行）と
配信系は不要になる。console が存在する理由は「認証付きのホストされた管理画面が無いから
手元に立てる」であり、artifact-share は Cognito + `upload-app.html` を持つのでその
存在理由自体が消える。

**根拠は spec 自身にある**

`bc-artifact-share`（VALIDATED）の概要が既にこう宣言している ——
「この文脈では、**共有される文書の中身を解釈しない**。何が書かれているかではなく、
誰が見られるか・いつまで見られるか・どんなコメントが集まったかだけを扱う」。
UIモックという語は spec のどこにも無く、design-share の成果物は「1つの完結した文書」の
一種にすぎない。`contextMap` には既に bc-waffle との「公開された言語」関係があり、
生成元が複数あることも織り込み済み。

**コメントレビューは既に artifact-share 側にある**（派生元なので当然）

- `share-wrapper.html:550` に `setInterval(..., 5000)` = 5秒ごとの同期（ライブレビュー）
- 返信・3択の判定（ただの意見／この方向でよいか／直してほしいか）はユビキタス言語に定義済み
- したがって design-share の Core value は artifact-share 側にある。design-share に
  コメント機能を残す理由は無い

**統合の方向（2026-08-05 に確定）**

design-share は配信を**一切持たない**。配る手段は artifact-share が所有し、その
呼び口が artifact-share 側の MCP（`scripts/mcp/server.py`、道具14個）。design-share は
拡張として artifact-share を前提にしてよいが、コードにも文書にも相手の名前を書かない。

- `artifact-share が design-share を取り込む` は**自分の spec と矛盾する**
  （名指しで知った瞬間「中身を解釈しない」が成り立たない）
- `design-share が配信を持ち続ける` も不可。ただし「前提として依存を宣言する」のは
  許され、禁じ手なのは「判定して分岐する」こと（[[feedback-skill-dependency-direction]]）
- 両者をつなぐのは HTML の自己記述メタデータ（id/type/title/description/tags）のみで、
  その取り決めは `infra/contract/document-meta.json` が所有する（所有者は読む側）

**この整理から出る帰結2つ**

1. design-share のモックテンプレートから**コメントUIを外す**。現行ガードレールは
   「コメントUIはページに内蔵し自己完結させる」だが、artifact-share は
   `content.html` を書き換えず `share-wrapper.html` で包んでコメントを提供する。
   両方あるとコメント欄が二重に出る
2. `confirm-design` は分解される。「レビューコメントを同伴エクスポート」は
   artifact-share の `export` なので design-share が呼ぶと依存方向違反。
   Orchestrator が export → design-share は DESIGN.md の確定配置だけを担う

**公開の入口（決着済み）**

`publish` は管理APIのアクションとして最初からある（`main.py` の `action` の既定値）。
無かったのは**ブラウザ以外から呼ぶ手段**だけで、それを MCP として新設した。
`artifactshare.py` にサブコマンドとして足すのは禁止——あれはクラウドの権限で動くため、
「招かれた者だけが公開できる」前提が権限を持つ人の手元で崩れる。MCP は合言葉で
本人確認を通るので抵触しない。この区別は architecture の規約に明文化済み。

**artifact-share に無い操作**: `rename`（表示名のみ変更）/ `project delete` /
`project export` / ローカルとクラウドの同期判定。**復活させない**——design-share が
持っていたから移す、という理由では足さない（[[feedback-design-share-delivery-is-not-restored]]）

関連: [[project-dependency-checks-and-preset-growth]]

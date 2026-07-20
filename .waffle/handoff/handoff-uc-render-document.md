## 概要

Documentを人間可読な成果物へ描画するusecaseの設計判断を実装へ引き継ぐ。

---

# Documentを人間可読な成果物へ描画する実装引き継ぎ：handoff-uc-render-document

## 引き継ぎ元spec

uc-render-document

---

## 完成イメージ

---

## 設計観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | table部品bullet列オプションのレイヤー境界 | 既存のcode/join/sep/markField/markSuffixと同型の列オプション追加であり、新しい抽象化ではなく既存の閉じた語彙への値追加。中核サブドメインの厳密な層分離を維持し、レイヤー境界・依存方向の懸念なし。承認。 |
| tech-lead-advisor | MD正本方針との一貫性 | bullet列はMD正本のプレーンテキスト（<br>区切り）としてのみ出力し、構造情報をviewer側へ渡さないこと。HTML非生成という既存方針と一貫させる。 |
| ddd-advisor | レンダリング都合による型設計の逆転を避ける | bulletで描画できるからという理由で配列化する順序（レンダリング側の都合が意味を定義する側の型設計を後追いで決める）は避けるべき。condition/rationaleは実物確認済みで既に読点連結された複数の独立論点のため、この基準に照らして正当な変更（単一トピックの説明文の機械分割ではない）。 |
| ddd-advisor | 撤回した誤った前提（記録として残す） | 初版でMembersBlock/ValueObjectsBlockのsection+each移行も対象としたが、現行DomainSpecSchema/v5をCLIで確認した結果、既に実装済みと判明したため対象から除外した。コンテキスト圧縮前の古いv4分析を確認せず引きずっていたことが原因。 |
| ddd-advisor | agentKindのenum拡張は不要 | ephemeralな一発委譲（agentKind=subagentの都度使い捨て）はそもそもdocument.jsonとして永続化・登録されない設計であるため、実際に永続化されるagentKind=subagentインスタンスは今回作るwaffle-subagentテンプレート1個のみになる。よってconfig.json側で既存discriminator値agentKind=subagentそのものに対してdeploy先を宣言しても、矛盾する実在インスタンスは存在せず、二重の真実源にはならない。新しいdiscriminator値の追加・schema版上げは不要。 |
| tech-lead-advisor | 既存のdiscriminator分岐規約への適用 | render_document.pyには既にdiscriminator値でdict分岐する規約が_select_template/_select_deploy/_select_field_mapの3箇所で確立済みで、discriminator値(spec_kind)自体も98行目で既に計算済み。新しい層・抽象化は不要で、既存規約を_resolve_tool_deploy_targetsに適用するだけでよい。 |

---

## 実装観点

| advisor | 観点 | 考慮事項 |
|---|---|---|
| tech-lead-advisor | unit | part_renderer.pyのbullet描画（配列→<br>箇条書き）を外部依存なしで検証する。RenderMetaSchema自体のJSON Schema構造検証もここに含む。 |
| tech-lead-advisor | integration | 既存document.json（condition/rationaleがstringのまま）に対する後方互換チェックの振る舞いを、ファイルI/Oポートの偽実装で検証する。 |
| tech-lead-advisor | contract | uc-patch-schemaのset_field操作で実schema JSONファイルのcondition/rationaleの型・x-render.columnsを正しく部分更新できるかを確認する。 |
| tech-lead-advisor | acceptance | CLI経由でvalidate→renderをend-to-endに通し、bullet列を持つDocumentが意図通りのMarkdownに描画されることを確認する。既存の代表document.json（uc-patch-schema.json / agg-document.json）を実際に移行し非回帰を確認する。 |
| tech-lead-advisor | 移行ロジックの分離 | 既存document.jsonのstring→array移行ロジックは、レンダリング規則（恒久ロジック）とは変更理由が異なる一過性の処理。part_renderer.py/RenderMetaSchema側に混入させず、別usecase（uc-patch-schemaのset_field呼び出し）として分離すること。 |
| tech-lead-advisor | unit | _resolve_tool_deploy_targetsにspec_kind引数を追加し、_select_field_mapと同じ「値が全てdictならdiscriminator分岐」判定が適用されることを外部依存なしで検証する。 |
| tech-lead-advisor | integration | config.jsonのtoolMappings.claude-code.Agentが入れ子構造（orchestrator/subagent）になっていても、既存Orchestrator系（agentKind=orchestrator）documentのdeploy先がCLAUDE.md/AGENTS.mdへ従来通り解決されることをファイルI/Oポートの偽実装で検証する（回帰テスト）。 |
| tech-lead-advisor | acceptance | agentKind=subagentのwaffle-subagent documentをCLI経由でvalidate→renderし、.claude/agents/waffle-subagent.mdへのsymlinkが実際に作られることをend-to-endに確認する。 |
| ddd-advisor | 前提確認 | 着手前に、discriminator_key(schema)がAgentSchema/v3で実際にagentKindを返すことをinvestigationで確認する（未確認のまま進めるとspec_kindがNoneになり入れ子マッピングが常に空になる静かな失敗モードになりうる、というtech-lead-advisorの付言）。 |

---

## 既知の制約・トレードオフ

- bullet:trueとjoin/sepが同一列に同時指定された場合の優先順位は両advisorのバックボーン範囲外。実装時の暫定方針: bulletが真ならjoin/sepを無視し、validateではエラーにしない。
- condition/rationaleのstring→array変更は既存document.jsonにとって後方互換性のない変更であるため、DomainSpecSchemaの版を上げた上で対象documentのみ新版へ移行する（v5自体は不変のまま維持する）。
- config.jsonのtoolMappings.claude-code.Agentのみを入れ子化し、codex.Agent（AGENTS.md）/Skill/Knowledgeのマッピングは変更しない（他ツール・他documentTypeへの影響を局所化する）。

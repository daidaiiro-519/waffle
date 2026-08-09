---
name: project_block_key_must_equal_block_type
description: 名前と実体を一対一にする。鍵（blockKey⇄blockType）も形（同じblockTypeが同じ構造）も
metadata:
  type: project
---

**名前と実体を一対一にする。**破れは2種類ある——**鍵**（blockKey が blockType と違う）と、**形**（同じ blockType が schema ごとに違う構造を持つ）。どちらも「その名前を見ても実体が決まらない」という同じ病気なので、**1つの作業として直す**（別々にやると同じ判断を2回する）。

**形の破れ（2026-08-09 調査）**: `SummaryBlock` は DomainSpecSchema では `items`、PlatformSpec / PresentationSpecSchema では `text`。`RoleBlock` は AgentSchema が `text`、SkillSchema が `items`。`TriggerBlock` は TemplateSchema だけ `openingLine` を余分に持つ。**「Summary と聞いても items か text か分からない」**状態。

**あわせて確認した、守られている作法（例外ゼロ）**: `x-prompt-query` はブロック直下に付く（160件すべて）／Block 定義は `blockType` の const を持つ（違反0）／kind ごとに書き分ける `x-prompt-write`（`{kind: 文言}` のオブジェクト形式）はその schema の kind を網羅する（欠落0）。**作法自体は在り、よく守られている。**

**schema の読み書きの実務**: schema は `waffle query --operation query_path --path <schemaのパス> --expression "@"` で読める（`{"type":"raw","content": "<全文>"}` が返る）。書き込みは `patch-schema --operation set_field --params '{"defName":…,"fieldPath":…,"value":…}'`。**`set_field` は存在しないパスには何もしないが、書ける場所には書いてしまう**ので、適用後は `render-blank-template` を再実行して文言が変わったかで確かめる（`changed=true` だけを信じない。実際に使われない場所へ書いて汚染を出した）。**kind ごとの x-prompt-write は `$defs.<Block>.properties.<field>.x-prompt-write.<kind>` に在る**（kind 分岐の中ではない）。

`blockKey` は `blockType` を camelCase 化したものと**一致しなければならない**（2026-08-08 決定）。2つの名前が要る唯一の正当な理由は「1文書に同じ型のブロックが複数入るとき、役割を言い分ける」ことだが、全schema・全discriminatorを走査して**該当0件**だった。理由が無いのに名前が2つあるため、片方が勝手にずれていた。

**Why:** 名前の分岐が、実際にバグを黙って通した。`lint_docstring.py:50` は `content["docstring"]` を引くが、この key は `Docstring`（実装）と `TestScenarioDocstring`（テスト）の**2つの概念**を指している。だから間違った規約を渡しても同じ鍵で引けてしまい、テストを実装用の規約で測って**397件の誤報**を出した。key が概念どおり分かれていれば、ブロックが見つからず即座に落ちていた。「範囲を導出する仕組みが無いから誤報が出た」のではなく、**名前が概念を裏切っていたから間違いが黙って通った**。これは `bc-waffle` が宣言する一語一義の、Waffle自身の語彙における違反でもある。

**How to apply:** ずれている箇所（115参照、実体は約20種）— `description`→Summary/Overview/Purpose（3通りの意味を持つ）、`docstring`→TestScenarioDocstring、`rules`→ArchitectureRules/CodingRules/TestRules/ToolIntegrationRules、`category`/`members`→SubdomainCategory/SubdomainMembers、PlatformSpecの`capacity`/`security`他。`description` が frontmatter の欄名であることは key を歪める理由にならない——描画側（`x-render`）で「`summary` ブロックを frontmatter の `description:` へ出す」と対応づければ済む。この規律自体を機械的な検知にできる（blockKeyをPascalCase化してblockTypeと一致するか）。schema全体に及ぶ改名で既存documentが全て追随するため、規模は大きい。

関連: [[feedback_read_all_standards_not_one_block]]（test-standardに専用のdocstring規約がある件。同じ衝突の別の現れ方）

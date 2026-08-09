---
name: feedback_no_pattern_names_in_spec_vocabulary
description: 仕様の語彙にパターンの名前を入れない。様式の語彙が使えるのは規約から下だけ
metadata:
  type: feedback
---

**仕様（DomainSpec）の語彙にパターンの名前を入れない。** `port` / `adapter` / `Primary` / `Secondary` / `repository` などは特定のアーキテクチャ様式に属する語で、様式を宣言しているのは規約（`architecture.layers.style` = 「ポートとアダプター（ヘキサゴナル）」）である。**その語彙が使えるのは規約から下（規約・実装）だけ**で、仕様はその上にあるので使えない。実装のdocstringが「Secondary Port」と書くのは正しく、規約まで辿れる。

**Why:** 2026-08-09、仕様に「外部へ求める能力」を宣言する概念を設計する際、その名前をどうするかが核心になった。`port` はヘキサゴナル、`repository` はDDDの戦術パターンだが永続化しか表せない。中立に見えた `Primary/Secondary` も Cockburn の Ports and Adapters の語彙だとユーザーに指摘された。**同じ日に3回、フレームワークの具体を無自覚に持ち込んでいる**——Pythonの構造、Railsの `app/` ディレクトリ、そしてこの語彙。いずれも「具体を持ち込むな」と議論している最中の、説明や例示の側で起きた。

**How to apply:** 概念に名前を付けるとき、**向きや役割を素の記述で言う**。例:「この操作が、自分の外にあるものとして必要とすること」。向き（外から呼ばれる／外を呼ぶ）はどのアーキテクチャにも存在し、**名前だけがパターンに属している**。パターン名を使いたくなったら、それは様式を1つ前提にしているサイン。あわせて、例示やディレクトリ名を出すときも出典を確認する（`app/models` はRailsの慣習であって規約が要求していない）。この規律は検知にもできる（仕様本文にパターン名が現れないか）が、語の一覧を持つことになるので導入は別判断。

関連: [[feedback_no_conditional_branching_in_architecture_rules]]（規約に場合分けを持ち込まない）、[[project_domain_folder_unit_is_kind_based]]

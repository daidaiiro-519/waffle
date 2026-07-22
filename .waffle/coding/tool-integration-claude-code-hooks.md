---
id: "tool-integration-claude-code-hooks"
type: "tool-integration"
title: "Claude Code Hooksが要求する成果物形式・配線契約：tool-integration-claude-code-hooks"
description: "Claude Code Hooksという仕組み自体が要求する、成果物（Hookスクリプト）の入出力契約とsettings.jsonへの配線方法を定める。個々のHookが何を検知しどう振る舞うかはHookSchemaの責務であり、ここでは扱わない。"
tags: ["tier:platform"]
schemaRef: "CodingSchema/v4"
---

# Claude Code Hooksが要求する成果物形式・配線契約：tool-integration-claude-code-hooks

## 概要

Claude Code Hooksという仕組み自体が要求する、成果物（Hookスクリプト）の入出力契約とsettings.jsonへの配線方法を定める。個々のHookが何を検知しどう振る舞うかはHookSchemaの責務であり、ここでは扱わない。

---

## 対象ツールと成果物種別

- **ツール**: claude-code
- **成果物種別**: Hook
- **公式ドキュメント**: https://code.claude.com/docs/en/hooks

---

## 成果物の構造契約

各Hookスクリプトは実行時にstdinでJSON payloadを受け取り、判定結果をstdoutへJSONで出力する薄いプロセス。PreToolUseはブロック可否、PostToolUseは追加コンテキスト通知のみで、両者は出力フィールドの組が異なる。

| フィールド | 必須度 | 説明 |
|---|---|---|
| tool_input（stdin） | 必須 | 発火元ツール呼び出しの引数（例: BashならcommandとしてBashコマンド文字列、Edit/WriteならfilePath）。イベント種別により中身が変わる。 |
| transcript_path（stdin） | 任意 | セッションのtranscriptファイルへのパス。過去のツール呼び出し履歴を確認したいHookが使う。 |
| hookSpecificOutput.hookEventName（stdout） | 必須 | PreToolUseまたはPostToolUseの固定文字列。出力先イベント種別と一致させる。 |
| hookSpecificOutput.permissionDecision（stdout） | PreToolUseのみ条件付き必須 | denyまたはallow。denyのとき対象ツール呼び出し自体がブロックされる。 |
| hookSpecificOutput.permissionDecisionReason（stdout） | permissionDecision=denyのとき必須 | ブロック理由の人間可読な説明文。 |
| hookSpecificOutput.additionalContext（stdout） | PostToolUseのみ任意 | ブロックせず、追加の文脈情報としてモデルへ渡す通知文。空なら何も出力しない（沈黙）のが規約。 |

---

## 配線方法

### .claude/settings.json#hooks.PreToolUse[]

- **配線方式**: registration-array

#### 補足

各要素はmatcher（正規表現、対象ツール名。例: "Bash"、"Edit|Write"）とhooks[].command（実行コマンド文字列）を持つ。1matcherに複数commandを登録すると全て直列実行される。

### .claude/settings.json#hooks.PostToolUse[]

- **配線方式**: registration-array

#### 補足

構造はPreToolUseと同型。イベント名（PreToolUse/PostToolUse）ごとに配列が分かれる。

### .claude/hooks/{scriptName}.py

- **配線方式**: single-file

#### 補足

settings.jsonのcommandから参照される実行ファイル本体。Waffleの慣行では実体を.waffle/hooks/配下に置きsymlinkする（HookSchemaのscriptRef参照）。

---

## 規約・落とし穴

| 種別 | 規約 |
|---|---|
| 必須 | settings.jsonへcommandを登録する前に、参照先スクリプトファイル（またはsymlink）を先に作成すること。順序を逆にするとBash呼び出し自体が登録の瞬間から全面ブロックされうる。 |
| 必須 | PostToolUseのadditionalContextは、検知内容が無いときは何も出力せず沈黙すること（毎回定型文を出すと通知が形骸化しノイズになる）。 |
| 推奨 | 同一イベント・同一matcherに複数commandを登録する場合、それぞれが独立プロセスとして起動する（プロセス起動コストが線形に増える）。関連する複数の判定をまとめたい場合は、1つのディスパッチャスクリプトに集約することを検討する。 |
| 推奨 | matcherの正規表現は対象ツール名（Bash/Edit/Write/Read等）に対してかかる。ファイルパスパターンでの絞り込みはmatcherではできず、スクリプト内部でtool_inputを見て判定する。 |

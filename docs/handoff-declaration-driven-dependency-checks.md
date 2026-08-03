# ハンドオフ: 宣言を読む依存検査と、プリセットを育てる経路

**作成日:** 2026-08-04
**到達コミット:** `a90897f`（`7dbfe83`〜の一連）
**状態:** 一区切り済み。中断中の作業なし。作業ツリーはクリーン、テスト652件・検査すべて整合

**背景:** CodingSchema を「そこから開発が進む単一の出どころ」にする、という方針の続き。
検出側（drift check）がコード内に写しを持たず、宣言だけを読む形へ寄せる作業を進めていた。
その過程で、宣言されているのに誰も読んでいない領域（層の依存の向き）と、
実践から更新される経路を持たない領域（プリセット）が見つかり、両方をつないだ。

---

## 1. 何が変わったか（要点）

| | 内容 |
|---|---|
| `check-layer-drift` 新設 | 層をまたぐ依存の向き違反＋循環依存（層内を含む）。8言語 |
| `scaffold fill` の修正 | 書き込み0件でも成功を返していた（今回2回踏んだ） |
| architecture の規約審査 | 19件 → 15件。削除ゼロ、統合4件ぶん・書き換え2件 |
| `update-coding-preset` 新設 | 実践で確かめた規約をプリセットへ戻す経路 |
| MCPサーバの有効化 | 起動手段が存在しなかった。24ツールでCLIと過不足なし |

### いちばん大きい変化

**宣言が読まれるようになった。** `layers[].path` と `mayDependOn` は長く宣言されていたが、
`grep -rn "mayDependOn" src/` はゼロ件だった。宣言を直しても、それが実装に効いたかを
確かめる手段が無い状態が続いていた。

---

## 2. 引き継ぐ上で先に知るべき5点

### 2-1. MCP は再起動後に有効になる

`.mcp.json` と `waffle-mcp`（`pyproject.toml` の scripts）を追加した。
**Claude Code を再起動すると `mcp__waffle__*` として24ツールが使える。**

再起動前は `uv run waffle ...` を使う。なお PreToolUse のガードフックが
`.json` を含む Bash コマンドを塞ぐため、CLI 経由の作業ではスクリプトファイルを
書いて実行する回り道が要る。MCP 経由ならこの回り道は不要になる。

### 2-2. advisor レビューが全面的に未実施

規約15件も、2つの Handoff の観点19件も、**すべて Orchestrator 単独の判断**。
`reviewStatus.findings` に `open` のまま残してある。

- `.waffle/documents/handoff/handoff-check-layer-drift.json`（11件 open）
- `.waffle/documents/handoff/handoff-update-coding-preset.json`（8件 open）

委譲できる設定のセッションで、`ddd-advisor` / `tech-lead-advisor` に当て直すこと。
**これが最優先の残タスク。**

### 2-3. 「プリセット」が正しい語彙

`src/waffle/domain/model/CodingPresets/python-hexagonal.json` のこと。CLI・スキーマ・ポート名すべてが
`CodingPreset` で統一されている。**「種」「種データ」と言い換えない**
（このセッションで混入させ、spec 67箇所・Handoff 35箇所を直した）。

### 2-4. 3スタックの現況

| スタック | 違反 | 循環 | 宣言漏れ | 未実装 | 意味 |
|---|---|---|---|---|---|
| waffle | 0 | 0 | 0 | 0 | 宣言と実装が一致 |
| artifact-share | 0 | 0 | 21 | 5層 | 規約はあるべき姿・実装は未着手 |
| typescript-hexagonal | 0 | 0 | 0 | 5層 | プリセットなので実装なし |

**artifact-share の21件と5層は「壊れている」ではなく「これから」。** 是正リストとして読む。

### 2-5. `docs/design-share-archive/` は未コミットのまま

34オブジェクト・実ユーザーのコメント14件を含む。**このリポジトリは公開**なので
コミットしていない。扱いは未決着（以前から持ち越し）。

---

## 3. 設計判断とその根拠

後から「なぜこうなっているか」を再導出せずに済むよう、判断の理由を残す。

### 3-1. ファイルを層へ割り当てる手がかりは置き場所だけ

`layers[].path` への前方一致（最長一致）で決める。ディレクトリツリーの図
（`layout.tree`）は**投影であって宣言ではない**ので参照しない。

この関係は `LayoutBlock` / `LayersBlock` の `x-prompt-query` に明記済み。
以前は `tree` の `x-prompt-write` が「正典ディレクトリツリー」と書き、
同じ欄の `x-prompt-query` が「機械はここから決定を読み取らない」と書いていて、
**書く側と読む側が矛盾していた**（`28f5913` で解消）。

### 3-2. 依存先の解決に、新しい宣言軸を足していない

依存の書き方は言語ごとに違う（ドット区切り・相対パス・モジュールパス・`::` 区切り）。
これを規約の欄として宣言させるとプロジェクトごとに埋める項目が増えるため、
**参照から候補パスを後ろ側から作り、規約の範囲の中に実在する最長のものを採る**。

実在確認は必須。**確認を省いたら、層と同じ名前を持つ外部ライブラリ
（`import shared` 等）を層への依存と取り違える誤検知が出た**（`17c57c4` で修正）。

### 3-3. 誤検知より見逃しを選んでいる

1つの並びだけからなる参照（`import domain`）がディレクトリにしか当たらない場合は
解決しない。「規約の中のパッケージ」と「同名の外部ライブラリ」を構文からは区別できず、
どちらと決めるにはプロジェクトの取り込み規約を宣言させる必要があるため。

**警報が信用できなくなる損失の方が大きい**という判断。見逃しの範囲は Handoff の
constraints に記録済み。

### 3-4. 循環は強連結成分で求める

層をまたぐ循環は `mayDependOn` が防ぐが、**同じ層の中の循環はどちらの向きも
許されているため、向きの規則では捕まらない**。深さ優先で辿った順に報告すると、
ファイルを見る順序という本質と無関係な要因で件数が変わるので、始点をどこに取っても
1件として返す形にした。

### 3-5. プリセットへは丸ごと写さない

戻す部分（`--blocks`）の指定を必須にした。プロダクトの規約には固有の判断が含まれる
（`coveredContexts` はプロダクト固有で、プリセットは持たない）。
**何が汎用かの判断は人が持ち、機械は反映だけを担う。**

反映はプリセットへの一方向のみ。双方向にすると、どちらが正かが場面ごとに変わる。

### 3-6. 規約は削除しなかった

適用対象が実装に存在しない3件（ロギング・監査ログ・認可）も残した。
**「いま使っていない」は取り下げの理由にならない。** 判断基準は
「今後そのケースを考慮する必要があるか」。規約が効くのはそのケースが現れた瞬間であり、
規約が無い状態で認可を足せば、まず domain に書く。

---

## 4. 開いている論点

優先順に。

### 4-1. advisor による規約レビュー（最優先）

2-2 のとおり。規約15件の妥当性も、2つの Handoff の観点も未検証。

### 4-2. artifact-share のコード是正

宣言漏れ21件・未実装5層。規約4文書（`*-artifact-share`）は**あるべき姿として**
書いてあるので、コードを宣言に沿わせる作業になる。

別トラックとして、閲覧の面（エッジゲートのトークン・交差条件）に対応する
usecase spec が15件の中に存在しない、という積み残しがある。

### 4-3. 外部ライブラリの閉じ込め検査（規約2）

**着手前に規約の妥当性を確かめること。** 旧規約7は「外部の作者が書いたコードか」と
「技術的詳細か」を混同していた（純粋な計算ライブラリを禁じ、自前コードのI/Oを見逃す）。
統合時に基準を書き直したので、その基準で検査できるかを先に判断する。

実装する場合、**SSOT は `pyproject.toml` / `package.json` 等の実ファイル**であるべき。
tech-stack の `libraries` は写しになっており、実測で **manifest 15件に対し3件しか
捉えていない**（しかも `^4` という npm 記法が Python の依存に混入している）。

あわせて `libraries` の役割を「一覧の写し」から「選定理由」へ改める案がある。
判断の単位はライブラリではなく**選定**（tree-sitter 9パッケージ＝1つの選定）。
15件 → 7件になる。これは依存検査とは独立した判断。

### 4-4. `init-coding-preset` の schemaRef が v4 固定

現行は CodingSchema/v5。プリセットから作られる document が v4 のままになる。

### 4-5. spec の語彙が既存の語彙と一致しているかの検査

2-3 の「種」混入を、いまの仕組みは検知できなかった。シナリオ・クラス名・操作名・
docstring は突き合わせているが、**語彙の言い換え**は見ていない。

### 4-6. `docs/design-share-archive/` の扱い

2-5 のとおり。

---

## 5. 引き継ぎ時の確認手順

グリーンを再現して現在地を確かめる。

```
uv run pytest -q
uv run waffle check-layer-drift --architectureRef architecture-waffle
uv run waffle check-scenario-drift --documentsRoot .waffle/documents/specs \
    --testsRoot tests --architectureRef architecture-waffle
uv run waffle check-spec-integrity --path .waffle/documents/specs/bc-waffle/bc-waffle.json
uv run waffle check-schema-version-drift
```

期待値: テスト652件・層の依存すべて0・シナリオ ペア45件/ドリフト0件・spec整合・schema版整合。

### 検査が本当に効いているかを疑ったとき

**0件が並ぶ検査は、壊れていて何も出ないのと見分けがつかない。** 実物へ違反を仕込んで
確かめること。

```
# 向きの違反（domain から application を参照するファイルを一時的に置く）
# → violations に1件出る

# 循環（同じ層の中で互いを参照する2ファイルを一時的に置く）
# → violations は0のまま cycles に1件出る
```

---

## 6. 関連ドキュメント

- `.waffle/memory/MEMORY.md` — セッションをまたぐ記憶の索引。作業開始時に読む
- `.waffle/memory/project_dependency_checks_and_preset_growth.md` — 同内容の要約
- `.waffle/memory/feedback_unused_is_not_a_reason_to_remove.md` — 繰り返している判断の誤り
- `.waffle/memory/feedback_x_prompt_is_the_core_not_metadata.md` — x-prompt の扱い
- `.waffle/handoff/handoff-check-layer-drift.html` — 依存検査の設計判断（HTML）
- `.waffle/handoff/handoff-update-coding-preset.html` — プリセット更新の設計判断（HTML）
- `.waffle/specs/bc-waffle/subdomain/sd-reconciliation/usecase/uc-check-layer-drift.md`
- `.waffle/specs/bc-waffle/subdomain/sd-document-management/usecase/uc-update-coding-preset.md`

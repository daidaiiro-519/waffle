# 別セッションへの引き継ぎ：artifact-share の未実装4件

2026-08-09 作成。**別のセッションがこの作業だけを引き取れるように書いた作業指示**であり、
設計判断そのものは既存の Handoff document が持つ（ここでは複製せず、指すだけにする）。

---

## やること

仕様は在るのに実装が無いものが4件ある。すべて `architecture-artifact-share` が
宣言する配置から導出された場所。

| 仕様 | 作るもの | 置き場所 |
|---|---|---|
| `agg-comment` | 集約ルート `Comment` | `.waffle/skills/artifact-share/lambda/admin_api/domain/comment.py` |
| `uc-post-comment` | `PostComment` | `.waffle/skills/artifact-share/lambda/admin_api/application/usecases/post_comment.py` |
| `uc-reset-password` | `ResetPassword` | `.waffle/skills/artifact-share/lambda/admin_api/application/usecases/reset_password.py` |
| `uc-sign-in` | `SignIn` | `.waffle/skills/artifact-share/lambda/admin_api/application/usecases/sign_in.py` |

**置き場所は自分で決めない。** 上の表は検知が宣言から導出した値をそのまま写したもので、
迷ったら `waffle check-usecase-class-drift --architectureRef architecture-artifact-share`
が `expectedPath` として教えてくれる。

---

## 前提は揃っている

- **仕様は4件とも VALIDATED**（`waffle query --operation get_meta` で確認済み）
- **引き継ぎ文書も在る。** 新しく作る必要は無い

読む順序：

1. `.waffle/handoff/handoff-artifact-share.html` — 配信基盤全体の設計観点と実装観点
2. `.waffle/handoff/handoff-artifact-share-layering.html` — 口を業務の語彙へ戻して層を分ける（`uc-reset-password` / `uc-sign-in` はこれが主）
3. `.waffle/handoff/handoff-artifact-share-aggregate-types.html` — 業務の語彙が住む場所をコードに作る（`agg-comment` / `uc-post-comment` はこれが主）

HTML が無ければ `waffle render-handoff-template --path .waffle/documents/handoff/<id>.json --outputPath .waffle/handoff/<id>.html` で作る。
**`waffle render` ではない**（HandoffSchema は `x-render-target` を持たないので `NO_RENDER_TARGET` になる）。

---

## 進め方

**TDD（Red → Green → 必要なら整理）。** 仕様のシナリオを先にテストへ転記し、落ちることを確かめてから実装する。

- テストの置き場所は `test-standard-artifact-share` の `placementByTarget` が宣言している。自分で決めない
- **シナリオは一字一句転記する。** 宣言行 `Scenario: {名前}` が突き合わせのキーになる（テスト関数の名前はキーにならない）
- 転記が合っているかは `waffle check-scenario-drift` の `gherkin_mismatches` で分かる

---

## 完了の測り方

```
waffle check-aggregate-class-drift --architectureRef architecture-artifact-share
waffle check-usecase-class-drift   --architectureRef architecture-artifact-share
waffle check-scenario-drift --documentsRoot .waffle/documents/specs/bc-artifact-share \
                            --testsRoot .waffle/skills/artifact-share/tests \
                            --architectureRef architecture-artifact-share
```

- 前2つの `missing_implementation_file` が **0件**
- 3つ目の `missing_in_tests` と `gherkin_mismatches` が **0件**
- artifact-share のテストが緑

着手前の値は `missing_implementation_file` が集約1件・ユースケース3件。

---

## 落とし穴（このセッションで実際に踏んだもの）

- **`--srcRoot` を手で渡さない。** 1階層ずれただけで「実装が無い」が7件出た。`--architectureRef` に導かせる
- **`scaffold fill` の戻り値 `written` を必ず見る。** 空なら書き込まれていない
- **配列は「query で現在値を取る → 組み立てる → fill で丸ごと置き換える」。** 部分更新はできない
- **document.json / schema は `waffle query` 経由でしか読めない。** `cat` / `grep` / `python3` はフックが止める
- **スクリプトはファイルへ書いてから実行する。** ヒアドキュメントの中に `.json` という文字列があるだけでフックが止める（既知の不具合）
- **セッション中、`.json` を fill した後に validate/render を促す通知が鳴り続けることがある。** 対象が既に消えていても鳴る（既知の不具合。無視してよい）

---

## 触らないもの

本セッションが並行で以下を触っている。**衝突するので手を出さないこと。**

- `src/waffle/domain/model/HookSchema/v1.json`
- `src/waffle/domain/model/CodingSchema/v5.json`
- `.waffle/documents/coding/test-standard-waffle.json`
- `.waffle/documents/hooks/` 配下
- `.waffle/hooks/` 配下
- `bc-waffle` 配下の仕様と `tests/` 配下

**artifact-share の木（`.waffle/skills/artifact-share/` と `bc-artifact-share` の仕様）は完全に独立している。**

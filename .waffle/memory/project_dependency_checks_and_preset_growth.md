---
name: project-dependency-checks-and-preset-growth
description: 2026-08-04時点の到達点。層の依存検査・循環検査・規約審査・プリセット更新・MCP有効化が完了し、残る論点はadvisorレビューとartifact-shareのコード是正
metadata:
  type: project
---

2026-08-04 に一区切りとした地点の記録。

**完了したこと**

- `check-layer-drift` を新設。宣言（layers[].path / mayDependOn）を唯一の基準に、
  層をまたぐ依存の向き違反を検出する。8言語対応。検査コードは層の名前も拡張子の表も
  持たない
- 同じ検査に循環依存の検出を追加。層をまたぐ循環は mayDependOn が防ぐが、
  **同じ層の中の循環は向きの規則では捕まらない**（どちらの向きも許されている）ため
- `scaffold fill` が書き込み0件でも成功を返していたのを修正。skip を「拒否（構造保護が
  働いた）」と「不正（呼び出し側の誤り）」に分け、不正があれば何も書かずに Err
- architecture の規約19件を審査し15件へ。すべてプリセット由来で一度も再検討されて
  いなかった。削除ゼロ、統合4件ぶんと書き換え2件
- `update-coding-preset` を新設。実践で確かめた規約をプリセットへ戻す経路。
  それまでプリセットは読み取り専用で、育てる手段が無かった
- MCPサーバを起動可能にした（`waffle-mcp` / `.mcp.json`）。それまで mcp.run() も
  登録も無く、定義はあるが一度も動かせない状態だった。24ツールでCLIと過不足なし

**Why:** 宣言は読まれて初めて効く。layers[].path と mayDependOn は長く宣言されて
いたが、どのコードも読んでいなかった（grep でゼロ件）。同じ理由で、プリセットは
実践から更新される経路が無く、欠陥が配られ続けていた。

**How to apply:**
- 新しい検査を足す前に、その根拠となる**規約自体が正しいか**を先に確かめる。
  規約7（domain/application が外部ライブラリを直接 import する＝禁止）は
  「外部の作者か」と「技術的詳細か」を混同した過剰な規約で、検査を作っていたら
  誤りを機械的に強化していた
- 検査を作ったら、**実物へ違反を仕込んで検出を確かめる**。0件が並ぶ検査は、
  壊れていて何も出ないのと見分けがつかない
- 3スタックの現況: waffle は全項目0（整合）。artifact-share は宣言漏れ21・未実装5層
  （規約をあるべき姿として書き、実装は未着手）。typescript-hexagonal は未実装5層

**未着手の論点**

- **advisor による規約レビュー**（本セッションは委譲不可の設定だったため未実施。
  handoff-check-layer-drift / handoff-update-coding-preset に findings が open で残る）
- artifact-share のコード是正（宣言漏れ21件・未実装5層）
- `init-coding-preset` が生成する document の schemaRef が CodingSchema/v4 固定（現行v5）
- 外部ライブラリの閉じ込め検査（規約の見直し後に判断。SSOTは package.json 等の
  実ファイルであるべきで、tech-stack の libraries は写しになっている。
  manifest 15件に対し tech-stack は3件しか捉えていない）
- spec の語彙が既存の語彙と一致しているかの検査（「プリセット」を「種」と言い換えた
  混入を、いまの仕組みは検知できなかった）
- `docs/design-share-archive/` の扱い（公開リポジトリのため未コミットのまま保留）

関連: [[feedback-unused-is-not-a-reason-to-remove]]
[[feedback-x-prompt-is-the-core-not-metadata]] [[scenario-test-pairing-coverage]]

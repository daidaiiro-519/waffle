---
id: "coding-standard-artifact-share"
type: "coding-standard"
title: "artifact-shareのコーディング規約を定めるCoding Standard：coding-standard-artifact-share"
description: "artifact-shareのコーディング規約（命名・スタイル・docstring）を定める。2つのランタイムを持つため、表記は主ランタイム（Python）を基準にし、エッジ側は言語の慣習に従う。"
tags: ["tier:backend"]
schemaRef: "CodingSchema/v5"
---

# artifact-shareのコーディング規約を定めるCoding Standard：coding-standard-artifact-share

## 概要

artifact-shareのコーディング規約（命名・スタイル・docstring）を定める。2つのランタイムを持つため、表記は主ランタイム（Python）を基準にし、エッジ側は言語の慣習に従う。

---

## 命名

### ファイル名

- **由来**: type
- **変換**: pascal-to-snake
- **拡張子**: .py

### 表記

| 対象 | 可視性 | 表記 | 接頭辞 |
|---|---|---|---|
| `module` |  | snake |  |
| `type` |  | pascal |  |
| `function` |  | snake |  |
| `field` |  | snake |  |
| `function` | private | snake | `_` |
| `constant` |  | upper-snake |  |

### 規範

| 適用先 | 規範 |
|---|---|
| 語彙 | 仕様のユビキタス言語に一致させる。閲覧・公開・招かれた利用者といった語を、実装都合で言い換えない |
| domain | ユビキタス言語のみで命名する。技術的接尾辞（Impl/DTO/Manager/Helper等）を付けない |
| application | 動詞＋目的語の業務操作として命名する（例: PublishArtifact、SuspendArtifact） |
| outbound adapter | 使用する技術名を明示してよい（例: S3ArtifactStore、KvsTokenStore）。port実装であることが責務そのものなので技術名を隠す理由が無い |
| エッジランタイム | JavaScriptの慣習（camelCase）に従う。主ランタイムの表記を持ち込まない |

---

## スタイル

| 種別 | 規約 |
|---|---|
| 必須 | 型注釈を公開関数の引数・戻り値に付ける |
| 必須 | 1関数＝1責務 |
| 禁止 | 循環 import |
| 必須 | importは標準ライブラリ／サードパーティ／ローカルの3グループに分け、グループ間を空行で区切る |
| 禁止 | エッジランタイムで自前モジュールを読み込む（実行環境が許さない） |

---

## docstring

- **スタイル**: Google スタイル docstring
- **構文の種類**: tagged
- **パラメータ**: Args:
- **戻り値**: Returns:
- **例外**: Raises:

### 必須とする対象

| 対象 | 可視性 | 必須 |
|---|---|---|
| `module` | any | ✓ |
| `type` | public | ✓ |
| `function` | public | ✓ |
| `function` | private | - |

### 要約行の書き方

「何をするか・いつ使うか」を1行の平叙文で。ソースを開かずに検索と判断ができる語を選ぶ。

```
def publish_artifact(deps: Deps, request: PublishRequest) -> Result[Artifact]:
    """アーティファクトを公開し、閲覧トークンを発行する。

    Args:
        deps: 外部との接点（保管・トークンの保管・時刻）。
        request: 公開したい中身と、招かれた利用者の証明。

    Returns:
        発行したアーティファクト。招かれていなければ拒否の結果。

    Raises:
        なし。失敗は結果型で返す。
    """
```

---

## 決定ルール

| 種別 | 規約 |
|---|---|
| 必須 | 公開要素に要約行つき docstring を書く |
| 禁止 | コードから導出できる情報を docstring に書く（型の列挙・実装手順の逐語説明） |
| 推奨 | コメントは「なぜ」を書く（「何を」は命名と要約行が表現する） |
| 必須 | エッジランタイムは層に分けられないため、業務ルールを実装した箇所には、それがどのシナリオに対応するかを文書コメントで明記する |

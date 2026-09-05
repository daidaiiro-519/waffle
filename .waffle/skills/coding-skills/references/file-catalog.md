# ファイル一覧 ── 雛形と、そこから作られる規約

## 概要

**規約の種類1つに、雛形1つが対応する。**
どの層に置くかは、その規約が依存する軸で決まる。

## 雛形と規約の種類

| 雛形 | 作られる規約 | 何を宣言するか | 種別 | 置かれる層 |
|---|---|---|---|---|
| `templates/style.md` | `style.md` | 綴りと書式の規則 | コーディング | 言語 |
| `templates/failure.md` | `failure.md` | 失敗の運び方の規則 | コーディング | 言語 |
| `templates/concurrency.md` | `concurrency.md` | 並行の単位と、共有の扱い | コーディング | 言語 |
| `templates/test-mechanism.md` | `test-mechanism.md` | テストが走る仕組みと書き方 | テスト | 言語 |
| `templates/toolchain.md` | `toolchain.md` | 言語の標準ツールと版 | 技術スタック | 言語 |
| `templates/layers.md` | `layers.md` | 構成要素と、要素ごとの責務 | アーキテクチャ | アーキテクチャ |
| `templates/dependency.md` | `dependency.md` | 依存の向きと、反転の有無 | アーキテクチャ | アーキテクチャ |
| `templates/test-boundaries.md` | `test-boundaries.md` | 確かめる単位の境界 | テスト | アーキテクチャ |
| `templates/layer-mapping.md` | `layer-mapping.md` | 要素を言語の仕組みで表す形 | アーキテクチャ | 言語 × アーキテクチャ |
| `templates/test-placement.md` | `test-placement.md` | テストの置き場所の規則 | テスト | 言語 × アーキテクチャ |
| `templates/contract.md` | `contract.md` | 外部との契約 | アーキテクチャ | 用途 |
| `templates/lifecycle.md` | `lifecycle.md` | 起動と終了 | アーキテクチャ | 用途 |
| `templates/acceptance.md` | `acceptance.md` | 保証する振る舞い | テスト | 用途 |
| `templates/test-strategy.md` | `test-strategy.md` | テストの重心・計画・観点の採否 | テスト | 用途 |
| `templates/stack.md` | `stack.md` | 採用するアーキテクチャ・実行環境・実行時の依存 | 技術スタック | 用途 |

## いま在る規約

**一覧は生成物として `constraints/INDEX.md` にある**（`python3 scripts/index.py` で作り直す）。

| 層 | 規約 |
|---|---|
| `lang.rust` | `style.md` ・ `failure.md` ・ `concurrency.md` ・ `test-mechanism.md` ・ `toolchain.md` |
| `lang.go` | 同じ5種 |
| `arch.hexagonal` | `layers.md` ・ `dependency.md` ・ `test-boundaries.md` |
| `arch.data-port` | 同じ3種 |
| `lang.rust+arch.hexagonal` | `layer-mapping.md` ・ `test-placement.md` |
| `lang.rust+arch.data-port` | 同じ2種 |
| `lang.go+arch.hexagonal` | 同じ2種 |
| `purpose.hook` | `contract.md` ・ `lifecycle.md` ・ `acceptance.md` ・ `test-strategy.md` ・ `stack.md` |
| `purpose.backend-api` | 同じ5種 |
| `purpose.mcp-server` | 同じ5種 |

## 出典

**37本すべての出典を、原文を落として照合した（2026-09-05）。**
原文は `sources/` に置き、`scripts/check.py` が
「その URL の原文を落としているか」「照合する文字列がその原文に在るか」を検証する。

| 数えたもの | 件数 |
|---|---|
| 落とした原文 | 41 |
| 照合した出典の行 | 61 |
| 検証で見つかった食い違い | **17件**（記憶で書いた文字列が原文に無かった。すべて直した） |

## まだ埋まっていないもの

| 何が | どこ | 埋める条件 |
|---|---|---|
| 記憶への接続に使う技術 | `purpose.backend-api/stack.md` | 扱うデータの形と量が決まったとき |
| 手順の実装（既存を採るか自前か） | `purpose.mcp-server/stack.md` | 提供する能力が決まったとき |
| `lang.go+arch.data-port` | ── | Go でその構成を採ると決めたとき |

**どちらも「まだ決めていない」と書いてある。**`《…》` の空欄は残っていない。

**空のマスは作らない。**
その層で決まらないことの規約は、置かない ── 言語の層に `layers.md` は無い。

## 参照するもの

| ファイル | 何のためか | 誰が読むか |
|---|---|---|
| `README.md` | 何が入っているか、別のリポジトリへの持ち出し方 | 持ち出すとき |
| `SKILL.md` | 書く手順 | 毎回 |
| `references/glossary.md` | 語の定義 | 迷ったとき |
| `references/axes.md` | 軸の定義と、値・軸を足す手順 | 規約を起こすとき |
| `references/sources.md` | 認める出典と、照合の仕方 | 規約を起こすとき |
| `references/layer-documents.md` | 層ごとに決められること | 規約を起こすとき |
| `references/test-perspectives.md` | テスト観点の一覧 | 用途の規約を起こすとき |
| `references/file-catalog.md` | この一覧 | どの雛形を写すか迷ったとき |
| `references/authoring.md` | 規約を起こす手順 | 規約を起こすとき |
| `scripts/README.md` | 機械が回すものの説明 | 集める・検証する・索引を出すとき |
| `scripts/collect.py` | 軸の値から規約を集める | 書く手順の Step 2 |
| `scripts/check.py` | 規約の形を検証する | 規約を足したとき |
| `scripts/index.py` | 索引を作り直す | 規約を足したとき |
| `constraints/INDEX.md` | 索引（**生成物。手で書き換えない**） | どの規約が在るかを見るとき |

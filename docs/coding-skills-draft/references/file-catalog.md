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

| 層 | 規約 |
|---|---|
| `lang.rust` | `style.md` ・ `failure.md` ・ `test-mechanism.md` ・ `toolchain.md` |
| `arch.hexagonal` | `layers.md` ・ `dependency.md` ・ `test-boundaries.md` |
| `arch.data-port` | `layers.md` ・ `dependency.md` |
| `lang.rust+arch.hexagonal` | `layer-mapping.md` ・ `test-placement.md` |
| `lang.rust+arch.data-port` | `layer-mapping.md` |
| `purpose.hook` | `contract.md` ・ `lifecycle.md` ・ `acceptance.md` ・ `test-strategy.md` ・ `stack.md` |

## まだ書いていない規約

| 層 | 書いていない規約 | 書く条件 |
|---|---|---|
| `lang.go` | 5種すべて | Go を使うと決めたとき |
| `lang.rust` | `concurrency.md` | 並行の扱いが要ると分かったとき |
| `arch.data-port` | `test-boundaries.md` | この構成でテストの単位を決めるとき |
| `lang.rust+arch.data-port` | `test-placement.md` | 同上 |
| `lang.go+arch.hexagonal` | 2種 | Go とヘキサゴナルを組み合わせるとき |
| `purpose.backend-api` | 5種すべて | バックエンドAPI を作るとき |
| `purpose.mcp-server` | 5種すべて | MCP サーバーを作るとき |

**空のマスは作らない。**
その層で決まらないことの規約は、置かない ── 言語の層に `layers.md` は無い。

## 参照するもの

| ファイル | 何のためか | 誰が読むか |
|---|---|---|
| `SKILL.md` | 書く手順 | 毎回 |
| `references/glossary.md` | 語の定義 | 迷ったとき |
| `references/axes.md` | 軸の定義と、値・軸を足す手順 | 規約を起こすとき |
| `references/sources.md` | 認める出典と、照合の仕方 | 規約を起こすとき |
| `references/layer-documents.md` | 層ごとに決められること | 規約を起こすとき |
| `references/test-perspectives.md` | テスト観点の一覧 | 用途の規約を起こすとき |
| `references/file-catalog.md` | この一覧 | どの雛形を写すか迷ったとき |
| `references/authoring.md` | 規約を起こす手順 | 規約を起こすとき |
| `scripts/README.md` | 機械が回すもの | 集める・検証する・索引を出すとき |

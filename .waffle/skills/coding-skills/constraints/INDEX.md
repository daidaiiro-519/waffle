<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->
# 規約の索引

## 概要

**この索引は生成物である。**
規約を足したら作り直す。手で書いた行は、次の生成で消える。

## 層ごとの規約

| 層 | 依存する軸 | 規約 | 宣言すること | 規則 |
|---|---|---|---|---|
| `arch.data-port` | architecture＝data-port | `dependency.md` | 依存の向き | ─ |
| `arch.data-port` | architecture＝data-port | `layers.md` | 層と、層ごとの責務 | ─ |
| `arch.data-port` | architecture＝data-port | `test-boundaries.md` | 確かめる単位の境界 | 5 |
| `arch.hexagonal` | architecture＝hexagonal | `dependency.md` | 依存の向きと、反転の条件 | ─ |
| `arch.hexagonal` | architecture＝hexagonal | `layers.md` | 層と、層ごとの責務 | ─ |
| `arch.hexagonal` | architecture＝hexagonal | `test-boundaries.md` | 確かめる単位の境界 | 4 |
| `lang.go` | language＝go | `concurrency.md` | 並行の単位と、共有の扱い | 4 |
| `lang.go` | language＝go | `failure.md` | 失敗の運び方 | 5 |
| `lang.go` | language＝go | `style.md` | 綴りと書式 | 5 |
| `lang.go` | language＝go | `test-mechanism.md` | テストが走る仕組みと、書き方 | 2 |
| `lang.go` | language＝go | `toolchain.md` | Go の標準ツール | ─ |
| `lang.go+arch.hexagonal` | language＝go ／ architecture＝hexagonal | `layer-mapping.md` | 層を Go の仕組みで表す形 | ─ |
| `lang.go+arch.hexagonal` | language＝go ／ architecture＝hexagonal | `test-placement.md` | テストの置き場所 | 4 |
| `lang.rust` | language＝rust | `concurrency.md` | 並行の単位と、共有の扱い | 4 |
| `lang.rust` | language＝rust | `failure.md` | 失敗の運び方 | 4 |
| `lang.rust` | language＝rust | `style.md` | 綴りと書式 | 4 |
| `lang.rust` | language＝rust | `test-mechanism.md` | テストが走る仕組みと、書き方 | 2 |
| `lang.rust` | language＝rust | `toolchain.md` | Rust の標準ツール | ─ |
| `lang.rust+arch.data-port` | language＝rust ／ architecture＝data-port | `layer-mapping.md` | 要素を Rust の仕組みで表す形 | ─ |
| `lang.rust+arch.data-port` | language＝rust ／ architecture＝data-port | `test-placement.md` | テストの置き場所 | 3 |
| `lang.rust+arch.hexagonal` | language＝rust ／ architecture＝hexagonal | `layer-mapping.md` | 層を Rust の仕組みで表す形 | ─ |
| `lang.rust+arch.hexagonal` | language＝rust ／ architecture＝hexagonal | `test-placement.md` | テストの置き場所 | 3 |
| `purpose.backend-api` | purpose＝backend-api | `acceptance.md` | 保証する振る舞い | 5 |
| `purpose.backend-api` | purpose＝backend-api | `contract.md` | 外部との契約 | ─ |
| `purpose.backend-api` | purpose＝backend-api ／ runtime＝resident | `lifecycle.md` | 起動と終了 | ─ |
| `purpose.backend-api` | purpose＝backend-api | `stack.md` | 採用するアーキテクチャ・実行環境・実行時の依存 | ─ |
| `purpose.backend-api` | purpose＝backend-api ／ runtime＝resident | `test-strategy.md` | テストの重心・計画・観点の採否 | 2 |
| `purpose.hook` | purpose＝hook | `acceptance.md` | 保証する振る舞い | 4 |
| `purpose.hook` | purpose＝hook | `contract.md` | 呼び出し元との契約 | ─ |
| `purpose.hook` | purpose＝hook ／ runtime＝per-invocation | `lifecycle.md` | 起動と終了 | ─ |
| `purpose.hook` | purpose＝hook | `stack.md` | 実行時に使うツールと依存 | ─ |
| `purpose.hook` | purpose＝hook ／ runtime＝per-invocation | `test-strategy.md` | テストの重心と計画 | 2 |
| `purpose.mcp-server` | purpose＝mcp-server | `acceptance.md` | 保証する振る舞い | 5 |
| `purpose.mcp-server` | purpose＝mcp-server | `contract.md` | 外部との契約 | ─ |
| `purpose.mcp-server` | purpose＝mcp-server ／ runtime＝resident | `lifecycle.md` | 起動と終了 | ─ |
| `purpose.mcp-server` | purpose＝mcp-server | `stack.md` | 採用するアーキテクチャ・実行環境・実行時の依存 | ─ |
| `purpose.mcp-server` | purpose＝mcp-server ／ runtime＝resident | `test-strategy.md` | テストの重心・計画・観点の採否 | 2 |

## 種別ごとの規約

| 種別 | 規約 |
|---|---|
| architecture | `arch.data-port/dependency.md` ・ `arch.data-port/layers.md` ・ `arch.hexagonal/dependency.md` ・ `arch.hexagonal/layers.md` ・ `lang.go+arch.hexagonal/layer-mapping.md` ・ `lang.rust+arch.data-port/layer-mapping.md` ・ `lang.rust+arch.hexagonal/layer-mapping.md` ・ `purpose.backend-api/contract.md` ・ `purpose.backend-api/lifecycle.md` ・ `purpose.hook/contract.md` ・ `purpose.hook/lifecycle.md` ・ `purpose.mcp-server/contract.md` ・ `purpose.mcp-server/lifecycle.md` |
| coding | `lang.go/concurrency.md` ・ `lang.go/failure.md` ・ `lang.go/style.md` ・ `lang.rust/concurrency.md` ・ `lang.rust/failure.md` ・ `lang.rust/style.md` |
| tech-stack | `lang.go/toolchain.md` ・ `lang.rust/toolchain.md` ・ `purpose.backend-api/stack.md` ・ `purpose.hook/stack.md` ・ `purpose.mcp-server/stack.md` |
| test | `arch.data-port/test-boundaries.md` ・ `arch.hexagonal/test-boundaries.md` ・ `lang.go/test-mechanism.md` ・ `lang.go+arch.hexagonal/test-placement.md` ・ `lang.rust/test-mechanism.md` ・ `lang.rust+arch.data-port/test-placement.md` ・ `lang.rust+arch.hexagonal/test-placement.md` ・ `purpose.backend-api/acceptance.md` ・ `purpose.backend-api/test-strategy.md` ・ `purpose.hook/acceptance.md` ・ `purpose.hook/test-strategy.md` ・ `purpose.mcp-server/acceptance.md` ・ `purpose.mcp-server/test-strategy.md` |

## 数

<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->

| 数えたもの | 件数 |
|---|---|
| 規約 | 37 本 |
| 層 | 10 |
| 規則 | 69 件 |
| 出典を持たない規則 | 0 件 |
| 出典の行 | 105 行 |
| 出典が指す原典 | 53 本 |
| 落としてある原典 | 54 本 |
| 承認が記録された規約 | 37 / 37 本 |

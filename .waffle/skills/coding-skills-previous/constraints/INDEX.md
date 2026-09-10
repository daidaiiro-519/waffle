<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->
# 規約の索引

## 概要

**この索引は生成物である。**
規約を足したら作り直す。手で書いた行は、次の生成で消える。

## 層ごとの規約

| 層 | 依存する軸 | 規約 | 宣言すること | 規則 |
|---|---|---|---|---|
| `arch.hexagonal` | architecture＝hexagonal | `dependency.md` | 依存の向きと、反転の条件 | ─ |
| `arch.hexagonal` | architecture＝hexagonal | `elements.md` | 構成要素と、要素ごとの責務 | ─ |
| `arch.hexagonal` | architecture＝hexagonal | `test-boundaries.md` | 確かめる単位の境界 | 7 |
| `lang.go+arch.hexagonal` | language＝go ／ architecture＝hexagonal | `element-mapping.md` | 構成要素を Go の仕組みで表す形 | ─ |
| `lang.go+arch.hexagonal` | language＝go ／ architecture＝hexagonal | `test-placement.md` | テストの置き場所 | 4 |
| `lang.go` | language＝go | `concurrency.md` | 並行の単位と、共有の扱い | 4 |
| `lang.go` | language＝go | `failure.md` | 失敗の運び方 | 5 |
| `lang.go` | language＝go | `style.md` | 綴りと書式 | 5 |
| `lang.go` | language＝go | `test-mechanism.md` | テストが走る仕組みと、書き方 | 2 |
| `lang.go` | language＝go | `toolchain.md` | Go の標準ツール | ─ |
| `lang.rust+arch.hexagonal` | language＝rust ／ architecture＝hexagonal | `element-mapping.md` | 構成要素を Rust の仕組みで表す形 | ─ |
| `lang.rust+arch.hexagonal` | language＝rust ／ architecture＝hexagonal | `test-placement.md` | テストの置き場所 | 5 |
| `lang.rust` | language＝rust | `concurrency.md` | 並行の単位と、共有の扱い | 3 |
| `lang.rust` | language＝rust | `failure.md` | 失敗の運び方 | 4 |
| `lang.rust` | language＝rust | `style.md` | 綴りと書式 | 4 |
| `lang.rust` | language＝rust | `test-mechanism.md` | テストが走る仕組みと、書き方 | 2 |
| `lang.rust` | language＝rust | `toolchain.md` | Rust の標準ツール | ─ |
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
| architecture | `constraints/arch/hexagonal/dependency.md` ・ `constraints/arch/hexagonal/elements.md` ・ `constraints/lang/go/arch/hexagonal/element-mapping.md` ・ `constraints/lang/rust/arch/hexagonal/element-mapping.md` ・ `constraints/purpose/backend-api/contract.md` ・ `constraints/purpose/backend-api/lifecycle.md` ・ `constraints/purpose/hook/contract.md` ・ `constraints/purpose/hook/lifecycle.md` ・ `constraints/purpose/mcp-server/contract.md` ・ `constraints/purpose/mcp-server/lifecycle.md` |
| coding | `constraints/lang/go/concurrency.md` ・ `constraints/lang/go/failure.md` ・ `constraints/lang/go/style.md` ・ `constraints/lang/rust/concurrency.md` ・ `constraints/lang/rust/failure.md` ・ `constraints/lang/rust/style.md` |
| tech-stack | `constraints/lang/go/toolchain.md` ・ `constraints/lang/rust/toolchain.md` ・ `constraints/purpose/backend-api/stack.md` ・ `constraints/purpose/hook/stack.md` ・ `constraints/purpose/mcp-server/stack.md` |
| test | `constraints/arch/hexagonal/test-boundaries.md` ・ `constraints/lang/go/arch/hexagonal/test-placement.md` ・ `constraints/lang/go/test-mechanism.md` ・ `constraints/lang/rust/arch/hexagonal/test-placement.md` ・ `constraints/lang/rust/test-mechanism.md` ・ `constraints/purpose/backend-api/acceptance.md` ・ `constraints/purpose/backend-api/test-strategy.md` ・ `constraints/purpose/hook/acceptance.md` ・ `constraints/purpose/hook/test-strategy.md` ・ `constraints/purpose/mcp-server/acceptance.md` ・ `constraints/purpose/mcp-server/test-strategy.md` |

## 雛形と規約の種類

**規約の種類1つに、雛形1つが対応する。**

| 雛形 | 何を宣言するか | 種別 | 置かれる層 |
|---|---|---|---|
| `templates/acceptance.md` | 保証する振る舞い | test | 用途 |
| `templates/concurrency.md` | 並行の単位と、共有の扱い | coding | 言語 |
| `templates/contract.md` | 外部との契約 | architecture | 用途 |
| `templates/dependency.md` | 依存の向きと、反転の有無 | architecture | アーキテクチャ |
| `templates/element-mapping.md` | 要素を言語の仕組みで表す形 | architecture | 言語 × アーキテクチャ |
| `templates/elements.md` | 構成要素と、要素ごとの責務 | architecture | アーキテクチャ |
| `templates/failure.md` | 失敗の運び方 | coding | 言語 |
| `templates/lifecycle.md` | 起動と終了 | architecture | 用途 |
| `templates/stack.md` | 採用するアーキテクチャ・実行環境・実行時の依存 | tech-stack | 用途 |
| `templates/style.md` | 綴りと書式 | coding | 言語 |
| `templates/test-boundaries.md` | 確かめる単位の境界 | test | アーキテクチャ |
| `templates/test-mechanism.md` | テストが走る仕組みと書き方 | test | 言語 |
| `templates/test-placement.md` | テストの置き場所 | test | 言語 × アーキテクチャ |
| `templates/test-strategy.md` | テストの重心・計画・観点の採否 | test | 用途 |
| `templates/toolchain.md` | 言語の標準ツールと版 | tech-stack | 言語 |

## 数

<!-- 生成物。手で書き換えない。`python3 scripts/index.py` で作り直す -->

| 数えたもの | 件数 |
|---|---|
| 規約 | 32 本 |
| 層 | 8 |
| 規則 | 65 件 |
| 出典を持たない規則 | 0 件 |
| 出典の行 | 110 行 |
| 出典が指す原典 | 56 本 |
| 落としてある原典 | 64 本 |
| 承認が記録された規約 | 32 / 32 本 |

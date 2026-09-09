# ファイル一覧 ── 雛形と、そこから作られる規約

## 概要

**規約の種類1つに、雛形1つが対応する。**
どの層に置くかは、その規約が依存する軸で決まる。

## 雛形と、置かれる層

**正は `scripts/_common.py` の `KINDS_BY_SHAPE` である。**
散文の表に置くと、表が腐り、表を守るための検査が要ることになる。
**実際にそうなったので、コードへ移した。**

**読むための表は `constraints/INDEX.md` の「雛形と規約の種類」に在る**
（`python3 scripts/index.py` が、コードと雛形の前置きから作り直す）。

| 知りたいこと | どこに在るか |
|---|---|
| どの雛形が、どの形の層に置かれるか | `scripts/_common.py` の `KINDS_BY_SHAPE` |
| 各規約が何を宣言するか ・ 種別 | 雛形と規約の前置き `declares:` ・ `category:` |
| 読むための一覧と数 | `constraints/INDEX.md`（生成物） |

**空のマスは作らない。**
その層で決まらないことの規約は、置かない ── 言語の層に `elements.md` を置かない。

## 出典と承認

原典は `sources/` に置き、`scripts/check.py` が
「規則ごとに出典の行が在るか」「その URL の原典を落としているか」
「承認が記録されているか」を検証する。

**数は `constraints/INDEX.md` に在る**（`python3 scripts/index.py` が書き出す）。
ここには書かない ── 手で書いた数は必ず腐る。

| 何を確かめるか | どこで |
|---|---|
| 検査と、それが守っている宣言の一覧 | `python3 scripts/check.py --contracts` |
| 機械では裁けないもの | 同上（人が見るものとして並べてある） |

## まだ埋まっていないもの

| 何が | どこ | 埋める条件 |
|---|---|---|
| 記憶への接続に使う技術 | `purpose.backend-api/stack.md` | 扱うデータの形と量が決まったとき |
| 手順の実装（既存を採るか自前か） | `purpose.mcp-server/stack.md` | 提供する能力が決まったとき |
| `purpose.frontend` | ── | その用途を採ると決めたとき |

**どちらも「まだ決めていない」と書いてある**。`《…》` の空欄は残っていない。

## 参照するもの

| ファイル | 何のためか | 誰が読むか |
|---|---|---|
| `README.md` | 何が入っているか、別のリポジトリへの持ち出し方 | 持ち出すとき |
| `SKILL.md` | 書く手順 | 毎回 |
| `references/glossary.md` | 語の定義 | 迷ったとき |
| `references/axes.md` | 軸の定義と、値・軸を足す手順 | 規約を起こすとき |
| `references/sources.md` | 認める出典と、原典の読み方 | 規約を起こすとき |
| `references/layer-documents.md` | 層ごとに決められること | 規約を起こすとき |
| `references/test-perspectives.md` | テスト観点の一覧 | 用途の規約を起こすとき |
| `references/file-catalog.md` | この一覧 | どの雛形を写すか迷ったとき |
| `references/authoring.md` | 規約を起こす手順 | 規約を起こすとき |
| `scripts/_common.py` | 規約を読み込む共通の部品 | scripts を直したとき |
| `scripts/relist.py` | 規則の一覧を、詳細の塊から書き出す | 規則を足す・直したとき |
| `scripts/README.md` | 機械が回すものの説明 | 集める・検証する・索引を出すとき |
| `scripts/collect.py` | 軸の値から規約を集める | 書く手順の Step 2 |
| `scripts/check.py` | 規約の形を検証する | 規約を足したとき |
| `scripts/index.py` | 索引と数を作り直す | 規約を足したとき |
| `scripts/tests.py` | scripts の振る舞いを確かめる | scripts を直したとき |
| `constraints/INDEX.md` | 索引（**生成物。手で書き換えない**） | どの規約が在るかを見るとき |

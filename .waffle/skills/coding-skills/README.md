# CodingSkills

**規約を集めて、それに従って書くための Skill である。**
Waffle を必要としない。Python 3 の標準ライブラリだけで動く。

## 別のリポジトリへ持ち出す

```
cp -r coding-skills <相手のリポジトリ>/.claude/skills/
```

**ディレクトリ1つで完結している。**
設定ファイルの追記も、依存の導入も要らない。

## 中身

| ディレクトリ | 何が在るか | 手で書くか |
|---|---|---|
| `SKILL.md` | 書く手順（軸を確かめる → 集める → 食い違いを見る → 振る舞いを先に置く → 照らす） | 書く |
| `references/` | 語彙・軸・出典・層ごとの規約・テスト観点・雛形の一覧・規約の起こし方 | 書く |
| `templates/` | 規約の種類ごとの雛形15本。**種類1つに雛形1つ** | 書く |
| `constraints/` | 規約37本。層ごとのディレクトリに置く | 書く |
| `constraints/INDEX.md` | 規約の索引 | **生成物。手で書かない** |
| `sources/` | 出典の原文41本。落とした日と `sha256` つき | 落とす |
| `scripts/` | 集める・検証する・索引を出す | 書く |

## 走らせる

| 目的 | コマンド |
|---|---|
| 場面に効く規約を集める | `python3 scripts/collect.py --lang rust --purpose hook` |
| 規約の形を検証する | `python3 scripts/check.py` |
| 索引を作り直す | `python3 scripts/index.py` |

**`collect.py` は、足りない規約が在れば名指しして終了コード 1 で止まる。**
止まったら書かず、`references/authoring.md` の手順で規約を起こす。

## 収録している層

| 軸 | 値 |
|---|---|
| 言語 | `rust` ・ `go` |
| アーキテクチャ | `hexagonal` ・ `data-port` |
| 用途 | `hook` ・ `backend-api` ・ `mcp-server` |
| 実行環境 | `resident` ・ `per-invocation`（用途の規約が指定する） |

**`lang.go+arch.data-port` は在りません。** Go でその構成を採ると決めたときに起こす。

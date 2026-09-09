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
| `constraints/` | 規約37本。**`<軸>/<値>` を重ねたフォルダに置く**（下を見よ） | 書く |
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
| アーキテクチャ | `hexagonal` |
| 用途 | `hook` ・ `backend-api` ・ `mcp-server` |
| 実行環境 | `resident` ・ `per-invocation`（用途の規約が指定する） |

**`purpose` に `frontend` は在りません。** その用途を採ると決めたときに起こす。

## 規約の置き方

**層とは、その規約が依存する軸の集合である。**階層ではない。
フォルダは `<軸>/<値>` を重ねて、その集合を1つの道で表す。
**軸の並びは 言語 → アーキテクチャ → 用途 → 実行環境 に固定する** ──
並びを決めないと、同じ集合が2通りの道になる。

```
constraints/
  arch/hexagonal/          {アーキ}          だけに依存する規約
  lang/rust/               {言語}            だけに依存する規約
  lang/rust/arch/hexagonal/    {言語, アーキ}  両方に依存する規約
  lang/go/
  lang/go/arch/hexagonal/
  purpose/hook/            {用途}            だけに依存する規約
  purpose/backend-api/
  purpose/mcp-server/
```

**軸を1本足した層は、足す前の層の中に入る。**
`lang/rust/arch/hexagonal/` は `lang/rust/` を狭めたものである。

**正は前置きの `layer:` と `axes:` である。**フォルダはその見せ方でしかない。
`check.py` が、前置きとフォルダの並びが両方向で一致するかを確かめる。

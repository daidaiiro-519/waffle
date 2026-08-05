---
name: artifactshare
colors:
  ink: "#1b2027"
  ink-soft: "#5b6472"
  ink-faint: "#65707b"
  paper: "#f4f2ee"
  card: "#ffffff"
  line: "#dcd8d0"
  line-soft: "#e9e5de"
  accent: "#2f5d63"
  accent-soft: "#e3edee"
  ok: "#4f7355"
  ok-soft: "#eaf1ea"
  off: "#716a61"
  off-soft: "#efece6"
  warn: "#8a672b"
  warn-soft: "#f7f0e1"
  live: "#b4553f"
  token-bg: "#1f2529"
  token-ink: "#f0ede6"
  token-gold: "#d9b26a"
  dark:
    ink: "#e8e5df"
    ink-soft: "#a9b0ba"
    ink-faint: "#8b939d"
    paper: "#16191c"
    card: "#1f2327"
    line: "#343a3f"
    line-soft: "#2a2f34"
    accent: "#7fb3ba"
    accent-soft: "#1e2c2e"
    ok: "#8ecbb6"
    ok-soft: "#1d2a23"
    off: "#928a7a"
    off-soft: "#26241f"
    warn: "#c9a05e"
    warn-soft: "#2b2419"
    live: "#d98a72"
    token-bg: "#0e1113"
    token-ink: "#f0ede6"
    token-gold: "#d9b26a"
typography:
  sans: '-apple-system, "Segoe UI", system-ui, "Hiragino Sans", "Yu Gothic", sans-serif'
  serif: '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif'
  mono: 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace'
  scale:
    micro: "10px"
    label: "10.5px"
    caption: "11px"
    meta: "11.5px"
    small: "12px"
    body: "12.5px"
    control: "13px"
    input: "13.5px"
    strong: "14.5px"
    section: "17px"
    page: "19px"
    brand: "20px"
  weight:
    normal: 400
    strong: 600
    number: 700
  leading:
    tight: 1
    text: 1.65
    prose: 1.7
rounded:
  xs: "4px"
  sm: "6px"
  control: "7px"
  field: "8px"
  panel: "9px"
  box: "10px"
  pill: "11px"
  card: "12px"
  dialog: "13px"
  chip: "14px"
  round: "50%"
spacing:
  hair: "2px"
  tight: "4px"
  snug: "6px"
  gap: "9px"
  inner: "11px"
  item: "13px"
  block: "16px"
  card: "18px"
  section: "22px"
components:
  button:
    font-size: "{typography.scale.control}"
    font-weight: "{typography.weight.strong}"
    padding: "8px 18px"
    radius: "{rounded.control}"
    primary:
      background: "{colors.accent}"
      border: "1px solid {colors.accent}"
      color: "#ffffff"
    ghost:
      background: "transparent"
      border: "1px solid {colors.accent}"
      color: "{colors.accent}"
    danger:
      background: "transparent"
      border: "1px solid {colors.live}"
      color: "{colors.live}"
    disabled:
      opacity: 0.55
  card:
    background: "{colors.card}"
    border: "1px solid {colors.line}"
    radius: "{rounded.card}"
    padding: "{spacing.card}"
  status:
    font-family: "{typography.mono}"
    font-size: "{typography.scale.micro}"
    padding: "3px 9px"
    radius: "{rounded.pill}"
    published:
      background: "{colors.ok-soft}"
      color: "{colors.ok}"
      border: "1px solid {colors.ok}"
    suspended:
      background: "{colors.off-soft}"
      color: "{colors.off}"
      border: "1px solid {colors.off}"
  token-plate:
    background: "{colors.token-bg}"
    color: "{colors.token-ink}"
    label-color: "{colors.token-gold}"
    radius: "{rounded.box}"
    padding: "16px 18px"
    value-size: "17px"
  dialog:
    background: "{colors.card}"
    border: "1px solid {colors.line}"
    radius: "{rounded.dialog}"
    max-width: "460px"
    backdrop: "rgba(20,22,25,.42)"
    title-font: "{typography.serif}"
    title-size: "{typography.scale.section}"
  field:
    font-size: "{typography.scale.input}"
    padding: "9px 11px"
    radius: "{rounded.field}"
    border: "1px solid {colors.line}"
    background: "{colors.card}"
    required-mark-color: "{colors.warn}"
  chip:
    font-size: "{typography.scale.caption}"
    padding: "2px 8px"
    radius: "{rounded.pill}"
    background: "{colors.accent-soft}"
    color: "{colors.accent}"
  focus-ring:
    outline: "2px solid {colors.accent}"
    offset: "2px"
---

## Overview

共有した文書を、誰に見せているかを決めるための画面群。読むための場ではなく、
**決めるための場**である。並ぶのは自分が公開したものと、いま渡している相手で、
そのどちらも「いま何が開けて何が開けないか」を一目で言えることが仕事になる。

扱うものの性質が2つある。ひとつは**取り返しがつく**もの（公開を止める・再開する・
中身を差し替える）。もうひとつは**取り返しがつかない**もの（閲覧トークンを無効に
する）。この2つが同じ見た目で並ぶと、押す瞬間に区別できない。色と語の両方で分ける。

もうひとつ、この画面群だけが背負うものがある。**一度しか表示されない値**——閲覧
トークンそのもの。画面を離れたら二度と取り戻せないので、その瞬間だけは他のどこ
よりも強く出し、離脱から守る。

## Colors

地は温かみのある紙色（`paper`）。アクセントは深い青緑（`accent`）1色に絞り、
それ以外は無彩色に近い階調で押さえる。装飾のための色を持たない——**色が付いて
いる箇所は、必ず何かの状態を表している**。

状態の色は4つで、それぞれ用途が重ならない。

| 色 | 表すもの | 使ってよい場所 |
|---|---|---|
| `ok` | 開けている（公開中） | 状態チップ・完了の印 |
| `off` | 止まっている（公開停止中） | 状態チップ・止まった行の地 |
| `warn` | いま判断が要る（期限が近い・上限に達した・必須） | 注記・期限の表示・必須の印 |
| `live` | 取り返しがつかない（無効化） | 破壊的操作のボタンと文字・エラー文 |

`accent` を状態に使わない。逆に、状態の4色を装飾や強調に流用しない。とくに `live`
は「元に戻せない」ことの符号なので、単に目立たせたいだけの箇所へ持ち込むと、本当
に戻せない操作の重みが薄まる。

暗い面（`dark`）は反転ではなく別に置く。地を沈め、`accent` を明るい側へ寄せて、
どちらの面でも文字が読める明度差を保つ。`token-*` の3色だけは、暗い面でも明るい
面でも同じ黒地に置かれるため、地色以外は共通のままにする。

## Typography

3種を役割で分ける。本文と操作は `sans`、見出しと題名は `serif`、値と記号は `mono`。

`serif` は画面の題・ダイアログの見出し・ブランドにだけ使う。ここが唯一の「読ませる」
面で、それ以外は「見つけさせる」面だから、書体を変えて役割の違いを持たせている。

`mono` は人が読む文ではなく、**取り違えると困るもの**に使う。閲覧トークンの値、
URL、識別子、状態チップ、日付。等幅であることが、写し取るときの正確さを助ける。

寸法は 10px から 20px までの12段。刻みが細かいのは、情報の密度が高い一覧画面で、
主・従・注記の3層を狭い行の中で作り分けるため。逆に言えば、**この段の外の寸法を
足さない**——足した時点で層が4つ以上になり、どれが主かが読めなくなる。

## Layout

一覧は行、詳細はダイアログ。画面遷移を増やさず、決める場から離れずに済ませる。

行は `1fr auto auto` の3列で、左に何であるか、中に判断材料（コメント数）、右に
状態と操作。狭い幅では判断材料が2行目へ回り、状態と操作は右に残る。**どの幅でも
「いま開けるか」と「操作できるか」は同じ位置にある**。

ダイアログは 460px を上限にする。ここで扱うのは1つの対象への1つの決定だけで、
横に情報を並べる必要がない。中身が増えるときは横ではなく面（`dlg-pane`）を切り替え、
一度に1つの問いだけを出す。

## Elevation & Depth

影は2種類だけ。カードとダイアログ。それ以外に浮かせる要素を作らない。

深さで意味を作っている箇所がひとつある。**閲覧トークンの板**（`token-plate`）は、
この画面群で唯一、地より暗く沈む面である。周囲がすべて紙色の上に立つ中で、ここ
だけが逆向きに沈むので、視線が最後に必ずここへ落ちる。一度しか表示されない値に
だけ許した扱いで、他の要素をこの地色にしない。

## Shapes

角丸は用途で段階を持つ。小さいものほど丸みを抑え（チップの `4px`）、面が大きく
なるほど丸める（カードの `12px`、ダイアログの `13px`）。押せるものは `7px`（ボタン）
と `8px`（入力欄）で、押せないものと角の丸さで区別できるようにしている。

完全な丸（`50%`）はアバターと完了の印だけ。丸は「人」か「済んだこと」を表す。

## Components

すべての部品はフロントマターのトークンから導く。**ここに無い値をその場で作らない**。
新しい状態が要るときは、まずトークンを足してから部品を組む。

- **ボタン** — 主・ghost・danger の3種。ダイアログの脚部では、やめる（ghost）と
  決める（主）を右端に並べる。破壊的な決定だけ danger にする。押せないときは
  `opacity` を落とし、なぜ押せないかを近くの注記が語る。
- **状態チップ** — 公開中と公開停止中の2つ。色だけでなく語も変える。
- **閲覧トークンの板** — 値を一度だけ示す面。見出しに「二度と表示できません」を置き、
  値は `mono` の 17px。コピーの手応えは押したボタンの上に返す。
- **ダイアログ** — 見出し・対象・本文・脚部の4段。取り返しのつかない決定には、
  「できなくなること」と「変わらないこと」を対で並べる（`keep`）。
- **入力欄** — 必須の印は `warn`。エラーは `live` で、入力欄の下ではなく脚部の直前に
  1つだけ置く。
- **フォーカスリング** — `accent` の 2px、offset 2px。すべての操作可能要素に付ける。

## Do's and Don'ts

**Do**

- 状態は色と語の両方で表す。色が見えない人にも同じ情報が届くようにする
- 取り返しのつかない操作は `live` と、戻せないことを明記した確認で挟む
- 一度しか表示されない値は、`token-plate` に置き、離脱の前に一度止める
- 上限・期限・件数のような「いま判断に効く数」は、判断する場所の近くに置く
- 押せない要素は消さずに残し、なぜ押せないかを近くで語る

**Don't**

- `accent` を状態に使わない。状態の4色を装飾に流用しない
- `live` を「目立たせたい」だけの理由で使わない
- 破壊的な操作を、閉じる・進むと同じ列に並べない
- 型の段（12段）に無い寸法を足さない。角丸の段も同じ
- 一度しか表示されない値を、確認なしに閉じられる面へ置かない
- 同じ一手を1つの面に2箇所置かない

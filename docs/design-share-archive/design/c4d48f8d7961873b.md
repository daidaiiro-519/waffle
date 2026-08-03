---
name: design-share LP
description: design-share自身をOSSツールとして紹介するLP。生成されるデザインの質と、デザイナー・非デザイナー双方が使える体験に価値がある。Editorial Warmを起点に、ヒーローは実際に生成されたUIモック画面を主役に据える。
archetype: Editorial Warm（対話の結果、配色・書体はこのまま採用すると決定済み。角丸は不可ではなくrounded.smとして正式採用）
colors:
  primary: "#22201C"
  secondary: "#6E6659"
  accent: "#A6432D"
  neutral: "#F6F1E7"
typography:
  display:
    fontFamily: Fraunces
    fontSize: 2.6rem
    fontWeight: 600
  h2:
    fontFamily: Fraunces
    fontSize: 1.5rem
    fontWeight: 600
  body-md:
    fontFamily: Source Serif 4
    fontSize: 1.05rem
    lineHeight: 1.8
  label-caps:
    fontFamily: Source Serif 4
    fontSize: 0.72rem
    letterSpacing: 0.14em
rounded:
  none: 0px
  sm: 6px
spacing:
  md: 24px
  lg: 48px
  xl: 96px
components:
  pull-quote:
    textColor: "{colors.primary}"
    typography: "{typography.display}"
  link:
    textColor: "{colors.accent}"
  surface:
    backgroundColor: "{colors.neutral}"
---

## Overview

design-shareが扱う中心的な成果物（DESIGN.md）は、実体としてはMarkdownで書かれた1本の原稿である。関係者によるレビューは、GUIキャンバスの図形を動かす操作ではなく、原稿の余白に手を入れる行為に近い——だからこそEditorial（原稿・出版）という語彙は比喩ではなく、この製品の実際の仕組みの直接の反映である。

この「原稿を読み、余白に書き込む」という実体から、各トークンの必然性を導く:
- **生成りの地（neutral #F6F1E7）**: 白紙の事務用紙ではなく、すでに読まれ・手が入れられた原稿の紙面。真っ白は「これから作る」段取り待ちの空白を意味してしまい、design-shareが実際に扱う「もう存在していて、今まさに読まれ・コメントされている原稿」という状態と矛盾する。
- **テラコッタのアクセント（accent #A6432D）**: 原稿に修正を入れる編集者の朱筆の色を、attackの強い純赤ではなく穏やかな焼き色に落としたもの。実際にaccentを使う場所（リンク・修正希望コメントの強調）は、この製品で実際に朱を入れる箇所そのものと一致する。
- **セリフ書体（Fraunces / Source Serif 4）**: 中心的な成果物が「操作するダッシュボード」ではなく「読む文書」である以上、本文はUI用のサンセリフではなく、読む文章のための書体を採る。Frauncesの強いコントラストは、原稿というより「出版物」に近い作り込みの質を、装飾ではなく実際に成果物が読まれ判断される対象であることの現れとして担う。

ヒーローは実際に生成されたUIモック画面とその上でコメントが実際に往復する様子を主役に据え、抽象的な説明より先に成果物そのものと、その場で機能する様子を見せる。

## Colors

- **Primary (#22201C):** 温度のあるほぼ黒。本文と見出し。
- **Secondary (#6E6659):** 補足情報・キャプション。
- **Accent (#A6432D):** 原稿に朱を入れる編集者の筆致の色。リンクと強調（＝実際に手が入る箇所）にのみ使い、面積は常に小さく。
- **Neutral (#F6F1E7):** すでに読まれ・手が入れられた原稿の紙面。真っ白（＝これから作る空白）は使わない。

## Typography

見出しはFraunces、本文はSource Serif 4。本文は1行65字前後・行間1.8を守る。

Fraunces（SemiBold 600の静的インスタンス）とSource Serif 4（Regular 400）を design-share の同梱フォントへ追加済み（`FONT:fraunces-600` / `FONT:source-serif4-400`）。見出し・h2ともFraunces 600に統一（500の別ウェイトは持たない）。

## Layout

1カラム中心。セクション間は最低48px、章の区切りは96px（spacing.lg / spacing.xl）。本文セクション・見出し・大きな面はrounded.none（直角）を保つ。トグルボタンやチップ等の小さな操作要素にはrounded.sm（6px）を使ってよい。ヒーローに実際に生成されたUIモック画面を主役として置くが、その額装（枠）は直角のまま（rounded.none）とする。

## Elevation & Depth

このデザインに影・立体的な階層は無い。紙のように完全にフラットで、要素の重なりや浮き上がりを一切表現しない（Editorial Warmの「紙の比喩」に由来）。要素間の区別は、影ではなく余白（spacing）と色のコントラストだけで行う。

## Shapes

面（カード相当の大きな矩形・額装枠・セクション）は常に直角（rounded.none）で、紙の比喩を保つ。ボタン・トグル・チップ・入力欄など、操作対象であることを示したい小さな要素にはrounded.sm（6px）を使ってよい——これは紙の比喩を壊す装飾ではなく、操作可能な部品であることを形で伝えるための機能的な丸みとして区別する。円形（アイコンの点等）は角丸の対象外として別途許容する。

## Components

pull-quoteとlink、地色を担うsurfaceのみ確定済み。ヒーローのモック額装枠・ボタン等、他のコンポーネントトークンは未確定。

## Do's and Don'ts

- Do: 段落の間隔より行間を優先して調整する（Editorial Warm由来）
- Do: ヒーローで実際の成果物（生成されたUIモック）を見せ、説明文より先に提示する。コメントが実際に届く様子（状態遷移）まで見せ、1状態だけの静止画で終えない
- Don't: カード・影（紙の比喩を壊す。Editorial Warm由来）。大きな面の角丸も同様に不可（rounded.noneを保つ）
- Do: 小さな操作部品（ボタン・トグル・チップ）にはrounded.sm（6px）を使ってよい

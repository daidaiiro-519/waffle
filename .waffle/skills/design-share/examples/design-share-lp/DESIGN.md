---
name: design-share LP
description: design-share自身をOSSツールとして紹介するLP。生成されるデザインの質と、デザイナー・非デザイナー双方が使える体験に価値がある。Editorial Warmを起点に、ヒーローは実際に生成されたUIモック画面を主役に据える。
archetype: Editorial Warm（起点。以降の対話でdesign-share固有の要望を反映）
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

design-shareの価値は、生成される設計そのものの質と、デザイナー・非デザイナー双方が同じ体験で関われることにある。Editorial Warmを起点に、温かい生成りの地と高コントラストのセリフ見出しで「作り込みの質」を体現する。ヒーローは実際に生成されたUIモック画面を主役に据え、抽象的な説明より先に成果物そのものを見せる。

## Colors

- **Primary (#22201C):** 温度のあるほぼ黒。本文と見出し。
- **Secondary (#6E6659):** 補足情報・キャプション。
- **Accent (#A6432D):** リンクと強調にのみ。面積は常に小さく。
- **Neutral (#F6F1E7):** 紙を思わせる生成り。純白は使わない。

## Typography

見出しはFraunces、本文はSource Serif 4。本文は1行65字前後・行間1.8を守る。

Fraunces（SemiBold 600の静的インスタンス）とSource Serif 4（Regular 400）を design-share の同梱フォントへ追加済み（`FONT:fraunces-600` / `FONT:source-serif4-400`）。見出し・h2ともFraunces 600に統一（500の別ウェイトは持たない）。

## Layout

1カラム中心。セクション間は最低48px、章の区切りは96px（spacing.lg / spacing.xl）。角丸は使わない（rounded.none）。ヒーローに実際に生成されたUIモック画面を主役として置くが、その額装（枠）のトークンはまだ決まっていない。

## Elevation & Depth

このデザインに影・立体的な階層は無い。紙のように完全にフラットで、要素の重なりや浮き上がりを一切表現しない（Editorial Warmの「紙の比喩」に由来）。要素間の区別は、影ではなく余白（spacing）と色のコントラストだけで行う。

## Shapes

角は常に直角。roundedトークンは`none: 0px`のみを持ち、他の丸みの値は定義しない。丸みを帯びた形は紙の比喩と矛盾するため、意図的に持たない。

## Components

pull-quoteとlink、地色を担うsurfaceのみ確定済み。ヒーローのモック額装枠・ボタン等、他のコンポーネントトークンは未確定。

## Do's and Don'ts

- Do: 段落の間隔より行間を優先して調整する（Editorial Warm由来）
- Do: ヒーローで実際の成果物（生成されたUIモック）を見せ、説明文より先に提示する
- Don't: カード・影・角丸（紙の比喩を壊す。Editorial Warm由来）

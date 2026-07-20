---
name: Editorial Warm
description: 出版系メディアやブランドジャーナルでよく見る雰囲気。読む体験そのものを主役にする。
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
    fontWeight: 500
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
---

## Overview

温かい生成りの地に高コントラストのセリフ見出し、赤褐色のアクセント1色。余白は贅沢に取り、角は立てる。
シグネチャは特大の引用符付きプルクオート。ページは「読み物」であり、UIは黒衣に徹する。

## Colors

- **Primary (#22201C):** 温度のあるほぼ黒。本文と見出し。
- **Secondary (#6E6659):** 日付・著者名・キャプション。
- **Accent (#A6432D):** リンクと強調にのみ。面積は常に小さく。
- **Neutral (#F6F1E7):** 紙を思わせる生成り。純白は使わない。

## Typography

見出しはFraunces（癖のあるセリフ）、本文はSource Serif 4。本文は1行65字前後・行間1.8を守る。
ラベルは小さな大文字＋広い字間で、本文と明確に役割を分ける。

## Layout

1カラム中心。セクション間は最低48px、章の区切りは96px。写真・図版は本文幅を超えて広げてよい（ブリード）。

## Components

プルクオートは本文の2.5倍角で、先頭に特大の引用符を装飾として置く（これが唯一の飾り）。
ボタンよりテキストリンクを優先し、下線は細く文字から離す。

## Do's and Don'ts

- Do: 段落の間隔より行間を優先して調整する
- Do: 図版キャプションはsecondary色の小さなセリフ
- Don't: カード・影・角丸（紙の比喩を壊す）
- Don't: アクセント色の面での使用（ボタン背景など大面積）

---
name: Playful Startup
description: コンシューマー向けアプリやLPでよく見る雰囲気。親しみと勢いを大切にする。
colors:
  primary: "#16151A"
  secondary: "#5F5C66"
  accent: "#FF6B5E"
  accent-2: "#B7A6F5"
  neutral: "#FFFFFF"
  surface: "#FAF8FF"
typography:
  display:
    fontFamily: Nunito
    fontSize: 2.8rem
    fontWeight: 800
  body-md:
    fontFamily: Nunito
    fontSize: 1rem
    lineHeight: 1.65
  label:
    fontFamily: Nunito
    fontSize: 0.8rem
    fontWeight: 700
rounded:
  md: 10px
  lg: 16px
  pill: 999px
spacing:
  sm: 8px
  md: 16px
  lg: 32px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
    padding: 12px 24px
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
---

## Overview

ほぼ黒の本文にコーラルと薄紫の2アクセント。主要な面にだけ大きめの角丸。
シグネチャは手描き風のアンダーライン装飾（見出しのキーワード1語にだけ引く）。

## Colors

- **Primary (#16151A):** 本文。真っ黒より柔らかい。
- **Accent (#FF6B5E):** 主ボタン・強調。行動を促す色。
- **Accent-2 (#B7A6F5):** 背景の面・イラスト・タグ。accentと同時に同じ要素へ使わない。
- **Surface (#FAF8FF):** カードの地。わずかに紫がかった白。

## Typography

Nunito一族で統一し、ウェイト差（400/700/800）で階層を作る。displayは思い切って大きく。

## Layout

角丸カードのグリッド。ただし角丸は「主要な面」（カード・ボタン・入力欄）だけに使い、
画像やページ全体には使わない。余白は標準〜広め。

## Components

主ボタンはピル型＋コーラル。ホバーでわずかに浮く（2px）。
手描き風アンダーラインはSVGで1本だけ用意し、ヒーロー見出しのキーワードにのみ敷く。

## Do's and Don'ts

- Do: 絵文字ではなく一貫したアイコンセットを使う
- Do: 空状態には行動を促す一言とイラスト
- Don't: 2つのアクセントを同一要素に重ねる
- Don't: 全要素への角丸適用（締まりがなくなる）

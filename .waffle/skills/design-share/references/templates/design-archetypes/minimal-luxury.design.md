---
name: Minimal Luxury
description: 高級小売やポートフォリオでよく見る雰囲気。沈黙と余白で価値を語る。
colors:
  primary: "#F3EEE4"
  secondary: "#8D8779"
  accent: "#B08D4A"
  neutral: "#101010"
typography:
  display:
    fontFamily: Cormorant Garamond
    fontSize: 3.2rem
    fontWeight: 300
  body-md:
    fontFamily: Cormorant Garamond
    fontSize: 1.1rem
    lineHeight: 1.9
  label-caps:
    fontFamily: Jost
    fontSize: 0.68rem
    letterSpacing: 0.28em
rounded:
  none: 0px
spacing:
  lg: 64px
  xl: 128px
components:
  divider:
    backgroundColor: "{colors.accent}"
    height: 1px
    width: 48px
  link:
    textColor: "{colors.primary}"
---

## Overview

ほぼ黒の地にアイボリーの文字、真鍮色は1画面に一箇所だけ。
シグネチャは1画面に1本だけの繊細な罫線＋真鍮アクセント。要素を足すのではなく削って作る。

## Colors

- **Neutral (#101010):** 地。純黒ではなくわずかに温度を持つ黒。
- **Primary (#F3EEE4):** 文字。純白は使わない。
- **Accent (#B08D4A):** 真鍮。罫線・番号・ホバー時の1点にのみ。面では絶対に使わない。

## Typography

displayは細いセリフを大きく、字間はわずかに詰める。ラベルは小さな大文字＋極端に広い字間（0.28em）で、
このコントラスト自体をアイデンティティにする。

## Layout

1画面1メッセージ。セクション間は最低64px、主要な区切りは128px。
グリッドは非対称（例: 左1/3を空ける）を恐れない。

## Components

区切り線は幅48px・高さ1pxの真鍮色で、中央またはテキスト頭に置く。
ナビゲーションはテキストのみ、ホバーで真鍮色に変わる。

## Do's and Don'ts

- Do: 写真は大きく、文字は少なく
- Do: 遷移はゆっくり（300ms以上）とだが、reduced-motionを尊重する
- Don't: ボタンらしいボタン（枠線1px＋余白で十分）
- Don't: 真鍮色の2箇所目（希少性が価値の源泉）

---
name: Technical Blueprint
description: 開発者向けツールやインフラ管理画面でよく見る雰囲気。正確さと検査可能性を体現する。
colors:
  primary: "#E8ECEC"
  secondary: "#93A3A6"
  accent: "#1FA8A0"
  neutral: "#14181B"
  surface: "#1C2226"
  grid-line: "#2A3236"
typography:
  h1:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: 500
  body-md:
    fontFamily: Space Grotesk
    fontSize: 0.92rem
    lineHeight: 1.6
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 0.78rem
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 0.85rem
rounded:
  sm: 2px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
components:
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.sm}"
  status-ok:
    textColor: "{colors.accent}"
  code-block:
    backgroundColor: "#101417"
    typography: "{typography.data-mono}"
---

## Overview

インク寄りの黒地にティール1色。ラベル・ID・値は等幅フォント、面は罫線グリッドで区切る。
シグネチャは図表・線画（構成図やフローを1px線で描く）。飾らないことが信頼の表現。

## Colors

- **Neutral (#14181B) / Surface (#1C2226):** 地とパネル。差はわずかで、境界は罫線が担う。
- **Accent (#1FA8A0):** 正常状態・アクティブ・リンク。エラーは慣習通り赤系を別途足してよい。
- **Grid-line (#2A3236):** この配色の主役。面ではなく線で構造を作る。

## Typography

UIはSpace Grotesk、識別子・値・ログは常にJetBrains Mono。この2書体の役割を絶対に混ぜない。

## Layout

罫線グリッド。パネルは1px罫線＋2pxの角丸（ほぼ直角）。密度は高くてよいが、
等幅による桁揃えと罫線で視線の迷いをなくす。

## Components

ステータスは`●`＋等幅ラベル。コードブロックは地より一段暗く。
構成図は装飾なしの1px線画で、ノードは罫線ボックス。

## Do's and Don'ts

- Do: タイムスタンプ・ID・数値は例外なく等幅
- Do: 折りたたみ・展開で情報の深さを制御する
- Don't: グラデーション・影・イラスト
- Don't: 等幅フォントの本文への使用（読み物はSpace Grotesk）

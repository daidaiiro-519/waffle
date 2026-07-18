---
name: Public Trust
description: 行政・公共サービス系でよく見る雰囲気。誰一人取り残さない読みやすさを最優先する。
colors:
  primary: "#0B0C0C"
  secondary: "#505A5F"
  accent: "#1D70B8"
  neutral: "#FFFFFF"
  focus: "#FFDD00"
  critical: "#D4351C"
typography:
  h1:
    fontFamily: system-ui
    fontSize: 2rem
    fontWeight: 700
  body-md:
    fontFamily: system-ui
    fontSize: 1.1rem
    lineHeight: 1.6
  label:
    fontFamily: system-ui
    fontSize: 0.95rem
    fontWeight: 700
rounded:
  none: 0px
spacing:
  sm: 10px
  md: 20px
  lg: 40px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.none}"
    padding: 12px 20px
  focus-ring:
    backgroundColor: "{colors.focus}"
---

## Overview

濃紺と市民感のある青1色、装飾ゼロ、コントラスト最優先。
シグネチャは「あえて無し」— 抑制そのものが個性であり、信頼の表現。

## Colors

- **Primary (#0B0C0C):** 本文。白地に対しコントラスト比を最大化する。
- **Accent (#1D70B8):** リンクとボタン。青＝操作可能、という慣習を裏切らない。
- **Focus (#FFDD00):** キーボードフォーカスの表示専用。省略は許されない。
- **Critical (#D4351C):** エラー表示専用。

## Typography

システムフォントを使い、読み込み遅延も見た目の癖もゼロにする。本文は1.1remと大きめ、
1行65字以内。太字は見出しとラベルのみ。

## Layout

1カラム、左揃え、最大幅は読みやすさ基準（約66ch）。センタリングしない。
フォームは1画面1質問を基本とし、進捗を常に示す。

## Components

ボタンは角丸なし・単色。リンクは常に下線。エラーは色だけでなくアイコン＋文言で示し、
「何が起きたか・どうすればよいか」を必ず書く。

## Do's and Don'ts

- Do: 全テキストでWCAG AAコントラストを満たす（AAAを目標）
- Do: フォーカスリングは太く目立たせる（消すことは絶対にしない）
- Don't: 装飾目的の画像・アイコン・色
- Don't: プレースホルダーをラベルの代わりに使う

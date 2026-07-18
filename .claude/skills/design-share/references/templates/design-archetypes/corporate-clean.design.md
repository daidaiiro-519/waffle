---
name: Corporate Clean
description: 業務SaaSのダッシュボードでよく見る雰囲気。情報密度と即読性を最優先する。
colors:
  primary: "#1C2733"
  secondary: "#5A6B7A"
  accent: "#2F6FED"
  neutral: "#F2F4F6"
  surface: "#FFFFFF"
  positive: "#1E8E5A"
  critical: "#C2372E"
typography:
  h1:
    fontFamily: IBM Plex Sans
    fontSize: 1.6rem
    fontWeight: 600
  h2:
    fontFamily: IBM Plex Sans
    fontSize: 1.15rem
    fontWeight: 600
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 0.9rem
    lineHeight: 1.55
  label-data:
    fontFamily: IBM Plex Mono
    fontSize: 0.78rem
    letterSpacing: 0.02em
rounded:
  sm: 4px
  md: 6px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 20px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: 8px 14px
  stat-tile:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
---

## Overview

深いスレートネイビーの文字と冷えた技術的ブルー1色。余白は詰め気味、角丸は小さめ。
シグネチャはハイライン罫線付きの数値タイル。判断に必要な数字が3秒で読めることが正義。

## Colors

- **Primary (#1C2733):** 見出し・本文の主要文字色。黒よりわずかに青い。
- **Secondary (#5A6B7A):** ラベル・キャプション・罫線。
- **Accent (#2F6FED):** 操作可能な要素と現在地の表示にのみ使う。装飾には使わない。
- **Positive / Critical:** 状態表示専用のセマンティック色。アクセントとは役割を分ける。

## Typography

見出しも本文もIBM Plex Sans一族で統一し、数値・コード・IDにはIBM Plex Monoを使う。
数値が縦に並ぶ場所ではtabular-numsを必ず有効にする。

## Layout

密度優先。カードの内側余白は12px基準、セクション間は20px。1画面に収まる情報量を最大化するが、
罫線と背景色の差で領域を区切り、余白の少なさを構造で補う。

## Components

主要ボタンはアクセント1色のみ。stat-tileは上辺に1pxのアクセント罫線を敷き、
値（大）＋ラベル（小・大文字）＋前期比（モノスペース）の3段で構成する。

## Do's and Don'ts

- Do: 状態はチップ・色・形の3重で符号化する（色覚多様性対応）
- Do: 表の数値は右揃え＋tabular-nums
- Don't: グラデーション・影による立体感の演出
- Don't: アクセント色を見出しや装飾に流用する

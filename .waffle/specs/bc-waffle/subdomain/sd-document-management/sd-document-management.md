---
id: "sd-document-management"
type: "subdomain"
title: "Documentの生成・読取・描画を担うサブドメイン：sd-document-management"
description: "AI に構造を推論させず、システムが決定的に Document を生成(scaffold)・読取(query)・描画(render)する中核の業務領域。waffle の差別化そのもの（Harness 原則と UDD ループ）を担う。"
tags: ["context:waffle"]
schemaRef: "DomainSpecSchema/v8"
---

# Documentの生成・読取・描画を担うサブドメイン：sd-document-management

## 名前

Document管理

---

## 概要

- AI に構造を推論させず、システムが決定的に Document を生成(scaffold)・読取(query)・描画(render)する中核の業務領域。waffle の差別化そのもの（Harness 原則と UDD ループ）を担う。

---

## サブドメイン分類

### 分類

中核

### 根拠

- 『AI に構造を推論させず システムが構造を持つ／Spec を正本にして陳腐化させない UDD ループ』は waffle の競争優位の源泉であり、既製品で置換できない。ゆえに中核。旧 sd-rendering（補完）はこの subdomain に統合した——描画(render)は宣言的 x-render の閉じた語彙・複数種の Mermaid 図生成まで複雑化しており、単純な CRUD/ETL ではなくなっている。この複雑さは Harness 原則という同じ差別化に資するものであり、理由のない複雑化ではないため『補完→中核』の変化基準に合致する。対象データ（Document）・差別化原理（Harness 原則）が scaffold/query と同一である以上、subdomain を分ける意味も薄れていた。

---

## 業務ユースケース一覧

- uc-scaffold-document
- uc-query-document
- uc-query-document-collection
- uc-render-document
- uc-render-blank-template
- uc-check-query-precedes-array-fill
- uc-check-path-is-projection
- uc-render-handoff-template
- uc-render-document-viewer

---

## 詳細設計ガイド

- 中核ゆえドメインモデルで厚く実装する。schema 走査による骨格生成・意味単位アクセス・x-render 宣言に従った機械描画は、いずれも自前の決定的コードで書き、外部ライブラリやテンプレートエンジンに委ねない。

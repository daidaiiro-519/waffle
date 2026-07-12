# Schema定義ファイル自体の作成・部分編集を担うサブドメイン：sd-schema-management

## 概要

- AIに構造を推論させず、システムが決定的にSchema定義ファイル自体を作成・部分編集（ブロック追加・リネーム等）する業務領域。Documentの値ではなくDocumentの型定義そのものを対象とする点でsd-document-managementと責務が異なる（agg-document/agg-schemaが既に別集約であるのと同型の区別）。

---

## サブドメイン分類

### 分類

中核

### 根拠

- Waffleの差別化の源泉であるHarness原則（AIに構造を推論させずシステムが構造を守る）を、Document生成だけでなくSchema自体の生成・編集にも適用する
- Schema編集の安全性（冪等性・後方互換性・最小diff）は既製品のJSON編集ツールでは代替できない、waffle固有の価値

---

## 業務ユースケース一覧

- uc-patch-schema

---

## 詳細設計ガイド

- Schema編集はDocument編集より一段リスクが高い（既存Documentの適合性を左右するため）
- 物理的な整形はagg-schemaが定める契約（json.dumps(indent=2, ensure_ascii=False)相当）に一意に従わせる
- 部分編集は素のdict操作＋契約整形で最小diffを保証する
- 後方互換チェック（既存instanceを壊しうる変更の検出）を書き込み前に必ず通す

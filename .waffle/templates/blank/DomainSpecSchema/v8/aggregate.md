---
id: "{{この文書を一意に識別する識別子。}}"
title: "{{MARK7MARK}}"
description: "{{MARK9MARK}}"
tags: "{{MARK5MARK}}"
---

# {{MARK7MARK}}

## 概要

- {{MARK9MARK}}

---

## 集約ルート

{{MARK39MARK}}

### 外部参照（ID）

- {{MARK40MARK}}

---

## エンティティ

### {{MARK43MARK}}（集約ルート）

{{MARK44MARK}}

| 属性 | 型 |
|---|---|
| **{{MARK47MARK}}**（識別子） | {{MARK48MARK}} |

---

## 値オブジェクト

### {{MARK52MARK}}

| 表す値 | 振る舞い |
|---|---|
| {{MARK53MARK}} | {{MARK54MARK}} |

| 属性 | 型 |
|---|---|
| {{MARK56MARK}} | {{MARK57MARK}} |

---

## 不変条件

| ルール | 守り方 | 根拠 |
|---|---|---|
| {{MARK60MARK}} | {{MARK61MARK}} | - {{MARK62MARK}} |

---

## ライフサイクル

```mermaid
stateDiagram-v2
    {{MARK66MARK}} --> {{MARK67MARK}}: {{MARK68MARK}}
```

### 遷移

| from | to | command | 条件 |
|---|---|---|---|
| {{MARK66MARK}} | {{MARK67MARK}} | {{MARK68MARK}} | {{MARK69MARK}} |

---

## コマンド

### {{MARK72MARK}}

{{MARK73MARK}}

| 前提 | 後 | 発行イベント |
|---|---|---|
| {{MARK74MARK}} | {{MARK75MARK}} | {{MARK79MARK}} |

| 引数 | 意味 |
|---|---|
| {{MARK77MARK}} | {{MARK78MARK}} |

---

## ドメインイベント

### {{MARK82MARK}}

#### 発行契機

{{MARK83MARK}}

#### ペイロード

| 項目 | 意味 |
|---|---|
| {{MARK85MARK}} | {{MARK86MARK}} |

---

## 不変条件シナリオ

### 背景

{{MARK115MARK}}

### {{MARK117MARK}}

| 分類 | 観点 |
|---|---|
| {{MARK118MARK}} | {{MARK119MARK}} |

```gherkin
{{MARK120MARK}}
```

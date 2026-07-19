# protect-render-output

## 目的

投影（document.jsonからのrender出力）への直接編集を防ぐ。原本（document.json/schema.json）自体はprotect-document-json.py/protect-raw-json-access.pyが別途保護しており、本Hookはそれと対になる投影側の保護を担う。

---

## いつ働くか

Edit/Write操作の直前

---

## 委譲先usecase

check-path-is-projection

---

## スクリプト実体

.waffle/hooks/protect-render-output.py

---

## ガードレール

- 新しい判定ロジックをこのHookスクリプトに持ち込まない。判定ロジックの変更はusecaseRefが指すusecase側で行う

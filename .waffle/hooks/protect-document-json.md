# protect-document-json

## 目的

document.json直接編集の禁止というCLAUDE.mdの運用ルールを機械的に強制する。

---

## いつ働くか

Edit/Write操作の直前

---

## 判定ロジック

Edit/Writeツールの対象パスが.waffle/documents/配下の.jsonファイルに一致する場合、常に拒否する。document.jsonはCLI/MCP経由（scaffold fill / clear_field / patch-schema）で編集すべきというCLAUDE.mdの運用ルールを、Edit/Write呼び出しの時点で機械的に強制する。例外は無い。

---

## スクリプト実体

.waffle/hooks/protect-document-json.py

---

## ガードレール

- 例外を設けない（schemaファイル側は対象外だが、document.jsonには一切の例外を作らない）

# protect-raw-json-access

## 目的

document.json/schemaファイルの直接「読み」を防ぐ。protect-document-jsonが直接「書き」しか見ていなかった穴（AIがpython3/cat/grep等で直接読んでいた事故）を塞ぐ。

---

## いつ働くか

Read操作の直前、およびBashコマンド実行の直前

---

## 判定ロジック

Bashコマンド文字列がcat/head/python3/grep等の生読み取りコマンドと、document.json（.waffle/documents/配下）またはschemaファイル（src/waffle/domain/model/配下）へのパスを同時に含む場合に拒否する。waffle CLI自体の呼び出し（query --operation index_scan/get_field/get_block等）とgit（diff/show/log等）は対象外とする。「AIは値だけ、構造は機械が守る」というHarness原則を読み取り側（Read/Bash）にも適用する。

---

## スクリプト実体

.waffle/hooks/protect-raw-json-access.py

---

## ガードレール

- waffle CLI自体の呼び出しとgitの履歴確認コマンドは対象外とする（構造検証・prompt付与を経由する正規経路を塞がないため）

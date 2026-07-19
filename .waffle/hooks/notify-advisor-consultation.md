# notify-advisor-consultation

## 目的

advisorとの組み合わせが必須なschema作成・更新が、実際にadvisorへ相談されずに行われた場合に気づける形で記録する。

---

## いつ働くか

Bash経由でwaffle scaffold create/fillが実行された直後

---

## 判定ロジック

Bash経由のwaffle scaffold create/fillが、advisorとの組み合わせが必須（skill-routerのroutingTableでblock/nudge指定）なschema家族のdocumentを作成・更新しようとしているとき、対応するadvisor Skillがこのセッション内で呼ばれた形跡があるかをtranscriptから確認し、無ければ通知する。skill-routerのroutingTable document.jsonを唯一の真実源としてCLI経由で毎回参照し、ハードコードしたファイルパターン表は持たない（内部実装はuc-query-documentのquery_path[--blockKey routingTable --expression @]でブロック全体を取得しており、廃止されたget_block操作には依存しない）。qa-advisorはこのdocument編集ベースのトリガーに馴染まないため対象外。

---

## スクリプト実体

.waffle/hooks/notify-advisor-consultation.py

---

## ガードレール

- ハードコードしたファイルパターン表を持たない。skill-routerのroutingTableを唯一の真実源とする（二重の真実源を作らない）
- 「本当に相談したか」の意図検証はPreToolUse denyでは信頼できないため、ブロックせず通知に留める

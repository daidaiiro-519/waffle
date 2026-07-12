# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{title.title}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。 |
| `{{summary.items[1]}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{ubiquitousLanguage.items[1].term}}` | 用語（この文脈での呼び名）。 |
| `{{ubiquitousLanguage.items[1].definition}}` | その用語が指すものを1文で。 |
| `{{members.items[1].kind}}` | メンバーの種別。下のenum（subdomain/aggregate/usecase）から選ぶ。見出しにはsubdomain→サブドメイン、aggregate→集約、usecase→業務ユースケースの日本語ラベルが使われる。 |
| `{{members.items[1].members[1]}}` | その種別のidを配列で列挙。（配列。この形式の行を必要な数だけ繰り返す） |
| `{{contextMap.items[1].counterpart}}` | 相手のbounded-context名。 |
| `{{contextMap.items[1].relationship}}` | 関係種別（パートナー/顧客・供給/腐敗防止層 等）。 |
| `{{contextMap.items[1].content}}` | 他bounded-contextと何を連係するかを1文で。例: 注文確定イベントを配送コンテキストへ連携。関係種別=パートナー/顧客・供給/従属/腐敗防止層/公開された言語 等。1 bc しか無ければ空。（任意ブロック：他bounded-contextとの連係が無ければcontextMapブロック自体を省略してよい） |

---

# {{title.title}}

---

## 概要

- {{summary.items[1]}}

---

## ユビキタス言語

| 用語 | 定義 |
|---|---|
| `{{ubiquitousLanguage.items[1].term}}` | {{ubiquitousLanguage.items[1].definition}} |

---

## 構成要素

### {{members.items[1].kind}}

- {{members.items[1].members[1]}}

---

## 文脈マップ

| 相手コンテキスト | 関係 | 内容 |
|---|---|---|
| {{contextMap.items[1].counterpart}} | {{contextMap.items[1].relationship}} | {{contextMap.items[1].content}} |

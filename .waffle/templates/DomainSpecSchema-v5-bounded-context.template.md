# {{documentId}}

## プレースフォルダー定義票

| プレースフォルダー | 記入する内容 |
|---|---|
| `{{タイトル}}` | 「業務エキスパートが理解できる日本語の説明：識別子」の形式で設定してください。説明部分はこのSpecが何であるかを業務語彙で簡潔に表す句（documentIdやクラス名をそのまま繰り返さない）。specKindがbounded-context/subdomain/aggregateの場合は、説明の末尾にその種別を表す語（bounded-contextなら「〜を行う境界づけられたコンテキスト」、subdomainなら「〜を担うサブドメイン」、aggregateなら「〜を守る集約」）を含め、読んだだけでこのSpecがDDDのどの構成要素かがわかるようにしてください（usecaseの場合はこの種別語を付けない）。識別子部分はspecKindに応じて設定する: usecaseの場合はcontent.name.operationNameと同じ値、aggregateの場合はcontent.aggregateRoot.nameと同じ値、bounded-context/subdomainの場合はdocumentIdをそのまま使う（識別子は既に別の構造化フィールドが正であり、ここでは表示のためだけに引用する。実装と乖離しても他のフィールドのように機械的ドリフト検知の対象にならないため、識別子以外の実装レベルの詳細をここに書き込まない）。（JSON上のフィールド: content.title.title） |
| `{{概要.論点1}}` | 論点ごとに列挙する（1〜2項目が目安）。この文脈/業務領域/集約/ユースケースが何かを1〜2文で（ドメイン語彙のみ・技術用語禁止）。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.summary.items[]） |
| `{{ユビキタス言語.項目1.用語}}` | 用語（この文脈での呼び名）。（JSON上のフィールド: content.ubiquitousLanguage.items[].term） |
| `{{ユビキタス言語.項目1.定義}}` | その用語が指すものを1文で。（JSON上のフィールド: content.ubiquitousLanguage.items[].definition） |
| `{{構成要素.項目1.種別}}` | メンバーの種別。下のenum（subdomain/aggregate/usecase）から選ぶ。見出しにはsubdomain→サブドメイン、aggregate→集約、usecase→業務ユースケースの日本語ラベルが使われる。（JSON上のフィールド: content.members.items[].kind） |
| `{{構成要素.項目1.メンバー1}}` | その種別のidを配列で列挙。（配列。この形式の行を必要な数だけ繰り返す）（JSON上のフィールド: content.members.items[].members[]） |
| `{{文脈マップ.項目1.相手コンテキスト}}` | 相手のbounded-context名。（JSON上のフィールド: content.contextMap.items[].counterpart） |
| `{{文脈マップ.項目1.関係}}` | 関係種別（パートナー/顧客・供給/腐敗防止層 等）。（JSON上のフィールド: content.contextMap.items[].relationship） |
| `{{文脈マップ.項目1.内容}}` | 他bounded-contextと何を連係するかを1文で。例: 注文確定イベントを配送コンテキストへ連携。関係種別=パートナー/顧客・供給/従属/腐敗防止層/公開された言語 等。1 bc しか無ければ空。（任意ブロック：他bounded-contextとの連係が無ければcontextMapブロック自体を省略してよい）（JSON上のフィールド: content.contextMap.items[].content） |

---

# {{タイトル}}

---

## 概要

- {{概要.論点1}}

---

## ユビキタス言語

| 用語 | 定義 |
|---|---|
| `{{ユビキタス言語.項目1.用語}}` | {{ユビキタス言語.項目1.定義}} |

---

## 構成要素

### {{構成要素.項目1.種別}}

- {{構成要素.項目1.メンバー1}}

---

## 文脈マップ

| 相手コンテキスト | 関係 | 内容 |
|---|---|---|
| {{文脈マップ.項目1.相手コンテキスト}} | {{文脈マップ.項目1.関係}} | {{文脈マップ.項目1.内容}} |

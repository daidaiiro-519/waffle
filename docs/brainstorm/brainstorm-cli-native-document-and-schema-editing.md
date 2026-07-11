# ブレインストーミング: document.json・Schemaの完全CLI/MCP経由化

**目的:** 「document.json操作は必ずCLI/MCP経由で行う」というCLAUDE.mdの運用ルールに、実際には例外（トップレベルフィールドの直接Edit、Schema定義ファイル自体の直接Edit）が常態化している現状を洗い出し、その例外を無くす方向で何が必要かを整理する。
**モード:** 問題解決→アイデア発散
**作成日:** 2026-07-11

---

## 発端: Bashで直接JSONを書き換えるという近道をした事故

TemplateSchemaの各documentで、`content`の外側にあるトップレベルフィールド`skillRef`を設定する必要があったが、`scaffold fill`は`content.*`のパスしか書き込めず「skipped」扱いになった。この時、CLAUDE.mdが定める正規の代替経路（Read→Editツール）を使わず、**Bashで`python3 -c "json.load...json.dump..."`を直接叩いて済ませてしまった**。

これはユーザーに指摘されて発覚した。実害（既存の手作業整形を壊す等）は無かったが、プロセスとして良くない近道であり、かつ「そもそもなぜこの近道をしたくなったか」を辿ると、**トップレベルフィールドを正規に書き込む手段がCLIに無い**という構造的な穴に行き着く。

---

## 現状の運用ルール（CLAUDE.md）の実態

| ケース | 現状の経路 | 備考 |
|---|---|---|
| document.jsonの`content`配下 | `waffle scaffold --operation fill` | 正規の経路として機能している |
| document.jsonのトップレベルフィールド（`subdomainRef`/`agentKind`/`skillRef`等、`content`の外側） | Read→Edit（直接編集） | CLAUDE.mdは「schemaに新規必須トップレベルキー追加時のみ」许容と書いているが、実際はこのセッション中、**新規作成した文書でも**トップレベルフィールドは常にこの経路を通っていた（例: `uc-check-usecase-class-drift.json`の`subdomainRef`、Templateの`skillRef`）。つまり例外というより常態 |
| Schema定義ファイル自体（`src/waffle/domain/model/*/v*.json`） | Read→Edit/Write（直接編集） | こちらはCLIによる書き込み経路がそもそも存在しない。今回のAgentSchema v2/TemplateSchema v1の新設・DefinitionOfDone→AcceptanceCriteriaのリネーム等、全てEdit/Writeで直接行った |

「document.json操作は必ずCLI/MCP経由で行う」という原則が、実態としては「contentブロックの中身だけ」に限定されており、documentの型（Schema）そのものと、documentの骨格を成すトップレベルフィールドは常に例外側に落ちている。

---

## ユーザーからの要望（2026-07-11）

> 基本的にdocument.jsonもSchemaもwaffleのcommand経由で更新できるようにしてほしい

これは2つの異なる粒度の話を含む:

1. **document.jsonのトップレベルフィールドも`scaffold fill`（またはそれに類する操作）で書けるようにする** — 比較的小さい変更。`fill`の対象パスを`content.*`限定から、document全体（`documentId`等の不変フィールドを除く）に広げる。
2. **Schema定義ファイル自体をCLI/MCP経由で編集できるようにする** — こちらは大きな設計課題。JSON Schemaという再帰的・自己記述的な構造（`$defs`・`properties`・`x-prompt-write`・`x-render`・`if`/`then`/`allOf`等）を、Waffle自身のdocument.jsonの仕組みでどう表現するか自体が未解決。

---

## 論点1: トップレベルフィールドのfill対応

比較的小さい変更で済みそうな見立て。検討すべき点:

- なぜ現状`fill`は`content.*`限定なのか（意図的な設計か、単に手が回っていないだけか）を`scaffold_document.py`の実装から確認する必要がある
- `documentId`/`documentType`/`schemaRef`のような不変・const値は引き続き対象外にすべき（作成後に変更されるべきでない）
- `subdomainRef`/`agentKind`/`skillRef`のような「discriminatorやref」系のフィールドは対象に含めるべき

## 論点2: Schema定義ファイル自体のCLI編集

未解決・要検討の大きな論点。考えられるアプローチ2つ:

**アプローチA: メタスキーマによる構造化**
JSON Schemaの記述形式自体を表現する`SchemaSchema`のようなメタschemaを新設し、`waffle scaffold create/fill`でSchema定義ファイル自体を生成・編集できるようにする。Waffle自身の哲学（モデルはコードに宿る、dogfooding）には最も忠実だが、JSON Schemaの再帰的・自己記述的な構造（`$defs`のネスト、`if`/`then`/`allOf`分岐、`x-render`のRenderMetaSchema参照等）をどこまで型で縛れるかが未知数。過剰に複雑なメタschemaになるリスクがある。

**アプローチB: 構造化されない汎用パッチ操作**
`waffle schema-patch --schemaRef X --path $.defs.Foo.properties.bar --value ...`のような、JSON Path/JSON Pointerベースの汎用書き込みコマンドを新設する。ガイダンス（x-prompt-write相当の手引き）は持てないが、実装コストは低い。Waffle自身が既に読み込んでいる標準JSON Schemaのメタスキーマ（`$schema`が指す`https://json-schema.org/draft/2020-12/schema`）で構造的な妥当性だけは検証できる（oneOf禁止等のWaffle独自不変条件は`check-schema-version-drift`等の既存reconcileが別途担保）。

どちらのアプローチを取るか、あるいは他の方法があるか、まだ結論は出ていない。

---

## 論点3: Bashでの近道を機械的に防ぐ（Hooks/permission）

document.json・Schemaの両方がCLI経由で完結するようになれば理想的だが、それでも「うっかりBashで直接いじる」という近道は原理的に可能であり続ける。これを機械的に矯正する案としてユーザーから提案されたのが、Claude CodeのHooks/permission設定による制御:

- Bashツールへの`PreToolUse`フック、または`.claude/settings.json`のpermission denyリストで、`.waffle/documents/`配下・Schema定義ファイルへの書き込み系コマンド（`python3 -c`での`json.dump`、`sed -i`、`>`/`>>`リダイレクト、`cp`/`mv`での上書き等）を、`uv run --project waffle waffle ...`（正規のCLI経由）**以外**の経路として検知・ブロックする
- `uv run --project waffle waffle scaffold/query/validate/render/check-*`は明示的に許可し続ける

トレードオフ: パターンマッチベースの制御なので完全ではない（迂回は可能）が、今回のような典型的な近道は確実に潰せる。論点1・2でCLI経由の正規経路が整備されれば、そもそも近道をする動機（正規の書き方が無い）自体が減る点も踏まえ、**論点1・2が本丸、論点3はその上に被せる機械的セーフティネット**という位置づけで整理する。

---

## 論点1: 調査結果と実装完了（2026-07-11）

`scaffold_document.py`/`fill_template.py`を読んだ結果、`fill`が`content.*`限定なのは**部分的に意図的、部分的に見落とし**と判明した。

- `build_fill_template(schema, content)`が最初から`"content"`という固定パスで`_walk_fill`を呼ぶ設計は意図的（モジュールdocstring通り「contentは業務データ、トップレベルは構造」という線引き）
- しかし`_create`の`_build_skeleton`は`documentId`・discriminatorキー・`content`の3つだけを特別扱いし、他の必須トップレベルフィールドは型からの空デフォルト値で埋めるだけ。CLIの`--contextRef`/`--subdomainRef`オプションは**パス計算にのみ使われ、document本体には反映されない**——これが、このセッション中「usecase specの`subdomainRef`が抜けていた」「Templateの`skillRef`が空だった」が繰り返し起きた根本原因だった

**実装済み**: `fill_template.py`に`build_top_level_fill_template(schema, protected)`を新設し、`content`外のトップレベルフィールドも`x-prompt-write`を持つ限り`fill`で書き込めるようにした（`documentId`とdiscriminatorキーは識別子・構造分岐として明示的に保護）。TDD先行で3件の受け入れテストを追加、全193件pytest通過・`check-schema-version-drift`/`check-spec-integrity`ともにクリーン。実際に`.waffle/documents/agent/waffle.json`のスキーマRefバンプ・Templateの`skillRef`設定で運用実績あり。

（`_build_skeleton`側でcreate時にCLIオプションを直接反映する改善は、今回は見送り。fillで正規に書けるようになったことで実害は解消したため）

---

## 論点2: 再現性・冪等性の再評価と実プロトタイプ（2026-07-11）

### 再現性についての評価の訂正

当初「meta表現から実ファイルを都度自動生成する」モデルを前提に評価し、`json.dump`再シリアライズによるフォーマット破壊（`CodingSchema/v2.json`事故と同型のリスク）を懸念していた。しかしユーザーからの指摘で前提を変更:

- **新規schema作成**は骨格の一回生成（今の`scaffold create`と同じ思想）に留め、再生成ループを発生させない
- **再現性はバイト同一性ではなく、バリデーションによる構造的妥当性の担保**で代替する（`agg-schema.json`の不変条件を独立コマンド化する）
- **部分編集**は「ファイル全体を再構築」ではなく「新規部分をテンプレートから生成しテキストとして差し込む」方式にすれば、既存部分のバイトに触れないためフォーマット破壊リスクは大幅に下がる

この3点により、当初「難所」としていた再現性の懸念はほぼ解消される。

### 実プロトタイプ: ブロック追加の実験（2回）

**v1（文字列アンカー一致）**: `TemplateSchema/v1.json`のコピーに新規`$defs`ブロックを追加。結果——生成JSONは有効、diffは追加行のみ（既存行のフォーマットは無傷）、Waffle自身の不変条件（oneOf禁止・x-render閉じた語彙）も満たした。ただし挿入位置の特定が手書きの文字列一致のため、2回目実行では既存の一致パターンが崩れていて**assertエラーで安全に失敗**するのみ（真の冪等性ではない）。

**v2（JSONソースマッピング）**: 手書きの再帰下降パーサでテキストを走査し、JSON pointerごとの文字位置（`{value_start, value_end}`）を記録する仕組みを自作し、これを使って挿入位置を構造的に特定するよう改善。結果——

- 挿入前に同名ブロック/プロパティの存在を確認し、既にあれば無変更で成功する**真の冪等性**を実証（2回目実行の出力が1回目と完全一致）
- 元のファイルを4スペースインデント・プロパティ順序変更という別書式に意図的に変形させた派生ファイルに対しても、正しい挿入位置を構造的に特定できることを実証（**書式非依存性**）。文字列アンカー一致方式ではここで確実に失敗していたはず

**v3（jsonpatch + json-source-map、2026-07-11）**: `uv add jsonpatch json-source-map`で実際に導入し、自作パーサ・自作diffロジックを置き換えた。

- 「何が変わったか」は`jsonpatch.make_patch(old, new)`に一任——目的の終端状態を渡すだけで差分が出るようになり、ブロック追加以外の操作にもコード変更なしで対応できる汎用性を獲得
- 冪等性は「diffが空なら書き込み自体が発生しない」という形で、個別の存在確認コードを書かずに自動的に手に入るようになった（v2より素直な実現）
- `json_source_map.calculate()`は自作パーサと同じ位置情報を返し、かつkeyの位置も最初から持つ（自作版はリネーム未対応だったが、これなら対応しやすい）
- **ただし、生成するテキストの体裁はライブラリでは一切解決しない**。`json.dumps`をそのまま使うと、配列が無条件に改行される・インデントが揃わない等、Waffleの手作業整形とはかけ離れた出力になった。これは当初懸念していた「スニペット生成のテンプレート化」がライブラリ導入だけでは代替できない、独立した課題であることを実証した

### Waffle流の整形を再現する独自シリアライザの試作

観察の結果、Waffleの手作業整形は「全フィールドがスカラーか」ではなく「1行に収めた時の長さ」でcompact/expandを判定していると分かった（ネストした構造でも1行にした結果が閾値内なら1行にする）。この規則で`render(value, indent)`を実装し、既存の`TemplateSchema/v1.json`の9ブロックに対して「パースして再度renderした結果が元のテキストと完全一致するか」を検証した。

- 閾値100文字で**9ブロック中6ブロックが完全バイト一致**
- 閾値を130文字に上げると、別のブロックが崩れて4/9に悪化した——これは「単一の閾値ルールでは100%再現できない」ことの決定的な証拠。元のファイル自体（このセッション中に人力で整形したもの）が、似た長さの構造に対して一貫していない書式選択をしている箇所があり、原理的にどんな単一ルールを選んでも全ブロックを同時には再現できない

**結論**: 生成スニペットの書式再現は、シンプルな長さベースのヒューリスティックで実用上十分な精度（6/9）に到達できるが、**人間の手作業整形の揺れそのものは原理的にアルゴリズムで100%再現できない**。この残差は「新規追加箇所は多少の書式の揺れを許容する」か、「新規追加後にformatter的な後処理（例えば一貫した閾値ルールで全体を整形し直す一回限りの移行）をかけて以後は機械整形に統一する」かの判断が必要になる。

### 実践的効果測定: 本物のリネーム作業の再現（2026-07-11）

ダミーブロック追加より難しい実例として、本セッションで実際に行った`AgentSchema/v2.json`の
`DefinitionOfDone`→`AcceptanceCriteria`リネーム（`$defs`キー名・`blockType` const・
プロパティキー名・`required`配列・`$ref`参照という5箇所にまたがる識別子リネーム）を、
`rename_block(text, old_short, new_short)`として実装し、機械的に再現できるか検証した。

**方法**: 実際にコミット済みの`AgentSchema/v2.json`（after）に逆方向リネームを適用して
「もし`DefinitionOfDone`のままだったら」という合成before状態を作り、それに順方向リネームを
適用した結果が、本物のafterファイルと一致するかを比較した。

**結果**:
- 順方向リネームの結果は、**実際にコミット済みの本物のファイルとバイト単位で完全一致**
- JSON Schemaとしての妥当性（`Draft202012Validator.check_schema()`）・Waffle自身の不変条件
  （oneOf禁止）も満たした
- 初回実装ではリネームの冪等性が無く、既にリネーム済みの状態に同じ操作を行うと`KeyError`で
  失敗した。「リネーム元が存在せず、リネーム先が既に存在するなら完了済みとみなし無変更で
  成功する」というガードを追加し、**1回目5箇所書き換え・2回目0箇所（無変更）**という
  真の冪等性を確認

**スコープ外として明示的に除外したもの**: 自由文中の言及（説明文中の「受け入れ基準
（AcceptanceCriteria）」等）。これは構造的なJSONパスではなく任意の文字列値内の部分文字列
であり、機械的な置換は誤爆リスクがあるため、意図的に対象外とした（人手判断のまま残す）。

**結論**: ダミーブロック追加という単純なケースだけでなく、複数箇所にまたがる実際のリネーム
作業も、構造的識別子の範囲では機械的に安全・正確に再現できることを実証した。

### 全schema横断での効果測定と、契約の正体の発見（2026-07-11）

TemplateSchema/v1（9ブロック）だけでなく、全11ファイル（248ブロック）に自作シリアライザを
広げて再現率を測ったところ、**14%（35/248）まで悪化した**。原因を調査した結果、Waffleの
schema群には**単一の書式が存在せず、少なくとも3種類の異なる整形スタイルが混在**していると
判明した:

1. 「短ければ1行にする」閾値ヒューリスティック（Agent/Template/Knowledge——今回のセッションで
   手作業整形したファイル）
2. 「常に展開する」（DomainSpec v2/v3/v4・PlatformSpec・PresentationSpec・SkillSchema）
3. 「キー長に応じた縦位置揃え」（CodingSchema）

さらに検証したところ、**2番目のスタイルは、Python標準ライブラリの
`json.dumps(schema, indent=2, ensure_ascii=False) + "\n"`の出力とファイル全体でバイト単位で
完全一致**していた。つまりこれは自作すべき新しいルールではなく、**既にこのリポジトリの
過半数（当時10ファイル中6ファイル）が従っていた既存の慣習**だった。

この契約が採用された場合の効果を、実際のconformantファイル（DomainSpecSchema/v4）に対する
ブロック追加・リネームで検証したところ、**素の`json.load`→dict書き換え→`json.dumps`
だけで、今日組み立てた自作パーサ・jsonpatch・独自シリアライザ（349行）と完全に同一の結果
（最小diff・冪等性）が、36行のコードで得られる**ことを確認した。つまり契約に従うファイルに
対しては、複雑な機構は不要だった。

### 契約の正式採用と全schemaファイルの移行（2026-07-11）

上記の発見を受け、以下を実施した:

1. **契約に従っていなかった5ファイル**（`AgentSchema/v1`・`AgentSchema/v2`・
   `TemplateSchema/v1`・`KnowledgeSchema/v2`・`CodingSchema/v2`）と`RenderMetaSchema/v1`を、
   内容（パース結果）が変わらないことを確認した上で`json.dumps(indent=2, ensure_ascii=False)`
   形式へ一括移行した
2. `agg-schema.json`の不変条件（`invariants`・`invariantScenarios`）に「Schemaファイル自体の
   物理的な整形は常に`json.dumps(schema, indent=2, ensure_ascii=False)`の出力と完全一致する」
   を正式に追加した
3. `tests/unit/domain/test_agg_schema.py`に
   `test_Schemaファイルの物理整形はjson_dumpsと完全一致する`を追加し、in-scope schema全件
   （7ファイル）に対してこの契約を機械的に検証するようにした

全200件pytest通過・`check-schema-version-drift`/`check-spec-integrity`ともにクリーン。
これにより、**Waffleが管理する全schemaファイルが、単一の決定的な整形契約の下に統一された**。

### 既存ライブラリ資産の調査

自作コンポーネントの一部は、枯れた既存ライブラリに置き換えられる可能性がある。

| 資産 | 用途 | 状態 |
|---|---|---|
| `jsonschema`（`Draft202012Validator.check_schema()`） | 生成/編集したschemaファイル自体がJSON Schemaとして構文的に正しいかを検証するゲート | **既に依存関係にあり追加コスト無し**。壊れたschemaで`SchemaError`が正しく出ることを実機確認済み |
| `json-source-map`（PyPI） | 今回自作したJSONソースマッパーと同等機能。BigInt/Map/Set等のエッジケース対応の実績があり、自作より枯れている | **導入済み（`uv add`、プロトタイプで動作確認済み）** |
| `jsonpatch`（PyPI、RFC 6902準拠） | `make_patch(old, new)`で2つのJSON構造の差分を標準形式（add/remove/replace/move/copy/test）で取得できる。「何が変わったか」の計算をこのライブラリに任せ、「どう安全にテキストへ反映するか」は自作のsource-map splicerに担わせる、という役割分担ができる。後方互換チェック（`required`配列への追加を検知する等）も、この差分結果をフィルタするだけで実装できそう | **導入済み（`uv add`、プロトタイプで動作確認済み）** |

後方互換チェック自体（「あるschema変更が既存instanceを壊すか」の一般判定）は、JSON Schema向けの決定版ツールはPythonエコシステムには薄く（OpenAPI/Avro向けの方が充実）、`jsonpatch`の差分結果に対してWaffle自身の狭いルール（`required`配列への追加のみ禁止、等）を当てるフィルタとして自前実装するのが現実的と判断。

---

## 次のアクション

1. ~~`scaffold_document.py`の`fill`実装を読み、`content.*`限定が意図的な設計かどうかを確認する~~ → 完了・実装済み（論点1）
2. ~~論点2（Schema定義ファイル自体のCLI編集）の再現性・冪等性を評価する~~ → 完了。プロトタイプv1/v2/v3で実証済み
3. ~~`json-source-map`・`jsonpatch`を実際に導入する~~ → 完了（`uv add`済み、プロトタイプv3で動作確認済み）
4. ~~生成スニペットの書式再現（Waffle流シリアライザ）を試作する~~ → 完了。長さベースの閾値ヒューリスティックで9ブロック中6ブロックが完全一致、残差は人的整形の揺れによる原理的な上限と判明
5. ~~実際のリネーム作業（複数箇所にまたがる識別子変更）を再現できるか検証する~~ → 完了。`rename_block`を実装し、本物のコミット済みファイルとバイト単位で完全一致することを確認。冪等性チェックも追加済み
6. ~~全schema横断で再現率を測定し、書式の実態を調査する~~ → 完了。単一シリアライザでは14%（35/248）まで悪化することが判明し、原因調査の結果Waffle内に3種類の異なる整形スタイルが混在していると判明。うち1つが`json.dumps(indent=2, ensure_ascii=False)`そのものであると特定
7. ~~契約を正式採用し、全schemaファイルをこの契約へ統一する~~ → 完了。`AgentSchema/v1・v2`・`TemplateSchema/v1`・`KnowledgeSchema/v2`・`CodingSchema/v2`・`RenderMetaSchema/v1`を移行し、`agg-schema.json`の不変条件・`test_agg_schema.py`の機械チェックとして明文化した（全200件pytest通過）
8. ~~後方互換チェックを実装する~~ → 完了。`schema_patch.check_backward_compatible`が`jsonpatch.make_patch`の差分から`required`配列への追加を検出する
9. ~~書き込み前バリデーションを組み込む~~ → 完了。`PatchSchema`usecaseが後方互換チェック→`Validator.check_schema()`（`Draft202012Validator.check_schema`をadapterに追加）の順に通し、違反時は一切書き込まない
10. ~~正式なusecase化に進む~~ → 完了（2026-07-12）。詳細は下記「usecase化の完了」を参照
11. 論点3（Hooks/permission設定）は、実運用でしばらく使ってみてから`update-config`スキルで実際に設定する

---

## usecase化の完了（2026-07-12）

まずCLAUDE.mdの原則（Usecase-Driven Development: 実装よりspecが先）を一度飛ばしかけ、ユーザーに指摘されて修正した。正しい手順（ddd-advisor相談→spec作成→実装）で以下を完了した。

**ddd-advisor相談**: 新usecaseは既存の`sd-document-management`（Document集約が対象）に混ぜるべきか、新subdomainを切るべきかを相談。`agg-document`/`agg-schema`が既に別集約である以上、責務が実質的に異なり（`ubiquitous-language.md`のr1c判定）、新subdomain`sd-schema-management`を切るべきと判断。

**spec化**: `sd-schema-management`（subdomain、category=core）と`uc-patch-schema`（usecase、operationName=PatchSchema）をフルにDomainSpecSchemaで作成。`bc-waffle.json`のmembers・`agg-document.json`/`agg-schema.json`の不変条件も整合させた。

**実装**:
- `domain/services/schema_patch.py`: `add_block`/`rename_block`/`check_backward_compatible`/`dump`（純粋関数、port不要）
- `application/usecases/patch_schema.py`: `PatchSchema`usecase（Result型、後方互換チェック→構文検証→書き込みの順序を保証）
- `Validator`ポートに`check_schema`を追加、`JsonSchemaValidator`adapterで`Draft202012Validator.check_schema`を実装
- `SchemaRepository`ポートに`resolve_path`を追加、`PackageSchemaRepository`adapterで実装
- CLI（`waffle patch-schema`）・MCP（`patch_schema`）両方に配線

**副産物のバグ修正**: spec作成時に`subdomainRef`が3回目のこのセッション中の同じ不具合で欠落しているのを発見。根本原因（`_build_skeleton`がCLIから渡されたref系パラメータをdocument本体に反映しない）を今度こそ修正し、TDDでの再発防止テストも追加した。

**検証**: 全224件pytest通過（domain単体9件・acceptance9件・integration3件・contract2件を新規追加）。`check-spec-integrity`/`check-schema-version-drift`/`check-usecase-class-drift`すべてクリーン。実際に`waffle patch-schema`をCLIから叩き、スクラッチのschemaファイルへのブロック追加が動作することを確認した。

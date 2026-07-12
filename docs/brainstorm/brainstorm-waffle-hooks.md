# ブレスト: WaffleにHooksを持たせる（drift検知トリガーとcommand実行の制御）

**作成日:** 2026-07-12
**経緯:** loop/goal型タスクオーケストレーションの検討（`docs/handoff-goal-loop-
orchestration.md`）を進める中で、「今のWaffleのループ設計はまだ弱い」という
評価と合わせて、Hooksという別の切り口が挙がった。目的が異なる2つの用途を
まとめて「Hooks」と呼んでいるため、まずこの2用途を分けて整理する。

---

## 用途1: 既存のdrift検知をHooksとして能動的にトリガーする

現状Waffleは`check-schema-version-drift`/`check-scenario-drift`/
`check-spec-integrity`/`check-operation-drift`という4種のdriftチェックを
CLI/MCP経由で**手動実行**する形で持っている（reconcileサブドメイン）。
これらは「気づいたときに手で呼ぶ」運用になっており、drift検知の仕組み自体は
あるが、いつ実行されるかはユーザー（あるいはAI）の裁量に委ねられている。

Hooksとして組み込むとは、例えば以下のようなタイミングで自動発火させることを
指すはず（未確定・要検討）:
- schema/spec/実装いずれかへの書き込み直後（PostToolUse相当）
- セッション終了時（Stop相当）
- 一定間隔（/loopの時間駆動パターンに相当）

## 用途2: 意図しないcommand実行を制御するガードレール

用途1とは別に、「AIが意図しないcommandを実行してしまう」ことそのものを防ぐ
制御としてのHooksという話も出た。これはdrift検知（事後発見）とは異なり、
**実行前に止める**という性質を持つ。例えば:
- `waffle` CLIを介さない生の`json.load`/`json.dump`によるdocument.json直接編集
  （このセッションで実際に発生した違反そのもの）
- spec-firstを飛ばしていきなりschema実装に入る動き（同じくこのセッションで
  発生。`docs/brainstorm/brainstorm-handoff-schema.md`参照）

これら2件はいずれも今回のセッション中に実際に発生した違反であり、
「事後にdriftとして検出する」（用途1）のではなく「そもそも実行させない」
（用途2）という別のアプローチがあり得るのではないか、という着想。

---

## 用途1と用途2の関係（未整理）

この2つは目的（能動的な検知タイミング vs 実行前の制御）が違うため、
同じ「Hooks」という語で一括りにしてよいかは要検討。Claude Code自体の
Hooks機構（PreToolUse/PostToolUse/Stop等のイベントにコマンドをバインドする
既存の仕組み）を参考にできる可能性があるが、Waffleの文脈でどう再解釈するか
（Waffle自身がCLI/MCPを持つツールである以上、Hooksの実装場所はWaffle内部か、
それとも呼び出し側ツール（Claude Code等）のHooks機構に依存する形にするかも
未定）は決めていない。

---

## Hook候補一覧（Spec・実装・会話ログからの抽出、2026-07-12）

既存の4 driftチェックのspec（summary、`waffle query`で取得）と、このセッション
自体の会話・ツール使用ログを突き合わせて、候補を用途1/2に分けて列挙する。
**あくまで候補の洗い出しであり、どれを採用するか・実装するかは未検討。**

### 用途1由来（既存drift検知の自動発火）— spec記述から抽出

| # | 候補 | 発火トリガー（案） | 根拠spec |
|---|---|---|---|
| 1 | schema版ずれ検知 | schemaファイル（`src/waffle/domain/model/*/v*.json`）への書き込み直後 | `check-schema-version-drift`: 「Document集約の実インスタンス群が持つschemaRefを、実在するSchemaの版集合と突き合わせ…Schemaが進化した際に既存Documentが気づかれず陳腐化するリスク」 |
| 2 | シナリオ⇔テスト乖離検知 | `tests/**/test_*.py`またはusecase spec（TestScenariosブロック）への書き込み直後 | `check-scenario-drift`: 「宣言するシナリオ名と、対応するテストファイルのtest_*関数名を突き合わせ、未実装のシナリオ・宣言に対応しない孤立テストを機械的に検出する」 |
| 3 | spec参照整合性検知 | `.waffle/documents/specs/**`配下への書き込み直後 | `check-spec-integrity`: 「宣言と実態がずれている箇所（宙に浮いた参照・未宣言の実体・不整合な相互参照）を機械的に検出する」 |
| 4 | operation名の実装乖離検知 | usecase実装（`src/waffle/application/usecases/*.py`）への書き込み直後 | `check-operation-drift`: 「specの自由記述にしか現れず実装から乖離しても誰も気づけない、という盲点を検出する」 |

4件とも「該当ファイル種別への書き込み直後（PostToolUse相当）」が自然なトリガー
候補に見えるが、書き込みの都度フル実行するとコスト・ノイズが大きい可能性があり
（例えば1回のセッションで同じschemaを10回編集する場合に10回走らせるか）、
バッチ化・デバウンスの要否は未検討。

### 用途2由来（実行前ガードレール）— このセッションの違反ログから抽出

| # | 候補 | 検知対象 | 実例 |
|---|---|---|---|
| 5 | document.json直接編集の禁止 | `.waffle/documents/**/*.json`へのEdit/Write（`waffle scaffold fill`/`patch-schema`を経由しないもの） | このセッション冒頭で発生。ユーザーに「なんでwaffleのcommandを介して修正がされていないんだ」と指摘された |
| 6 | spec-first違反（spec無しでのschema実装着手）の禁止 | `src/waffle/domain/model/*/v*.json`への新規Write（対応するusecase specが`.waffle/specs`に存在しない状態） | `HandoffSchema/v1`を無spec状態で実装し、後に全撤去して`brainstorm-handoff-schema.md`へ差し戻した（[[feedback-udd-implementation-before-spec]]参照） |
| 7 | RenderMetaSchemaの閉じた語彙（x-render等）違反の禁止 | schemaファイルへの書き込み時、`x-render`等の値が定められた語彙外である場合 | 既に`agg-schema`のlint不変条件・`test_agg_schema.py`として**テストレベルでは**存在するが、Hookとして書き込み前に止める形にはなっていない（現状は書いてからテストで気づく） |

候補5・6はいずれも「AIがCLI/MCPを経由せず直接ファイル操作した」という共通パターン
であり、統合できる可能性がある（対象パスのパターンだけが違う）。候補7は既存の
テストレベルのガードを「書き込み前」に前倒しできないか、という発想で、用途1の
driftチェックとも性質が近い（=事後の自動テスト実行をHook化する話とも読める）。

---

## 実現可能性の検討（2026-07-12）

前述の「用途2はWaffle単体では実現できず、呼び出し元ツールのHooks機構が必須」
という論点を前提に、**現に今このセッションがClaude Code Hooks機構の上で
動いている**（`PreToolUse`/`PostToolUse`等のイベントにシェルコマンドをバインド
できる、`.claude/settings.json`で設定する既存の仕組み）ことを踏まえて、
候補1〜7を実現可能性の観点で分類する。

### 高: 既存のCLIチェックをPostToolUseで叩くだけ（候補1〜4）

`check-schema-version-drift`/`check-scenario-drift`/`check-spec-integrity`/
`check-operation-drift`はいずれも**既に実装・テスト済みのCLIコマンド**として
存在する。PostToolUseフックは「どのファイルパスに書き込まれたか」を
`tool_input`から取得できるため、対応するファイルパターン（schema/test・spec/
usecase実装）にマッチしたときに該当CLIを叩くだけで成立する。**Waffle側の
ドメインコードは1行も増やさず、フックスクリプト＋`.claude/settings.json`の
設定だけで成立する**という意味で実現コストが低い。

懸念点として「対象範囲全体を毎回スキャンする設計（差分だけを見る設計になって
いない）ため、書き込みの都度フル実行するとコストが重いのでは」と想定していた
が、**4チェックとも実測したところ杞憂だった**（後述シミュレーション参照。
実行時間はいずれも0.12〜0.17秒）。デバウンスや差分ベース化は現時点では不要と
判断してよさそうというのが実測に基づく暫定結論。

### 高: document.json直接編集の禁止（候補5）

CLAUDE.mdの規律は「document.json操作は必ずCLI/MCP経由」で**例外なし**
（唯一の例外は候補6と混同しやすいがそちらはschemaファイル側の話）。
これは`.waffle/documents/**/*.json`へのEdit/Write呼び出しをパスパターンで
機械的に検出でき、例外条件の判定（「本当にCLI経由か」を確かめる必要がない、
単に「Edit/WriteツールでこのパスにマッチしたらCLIを使わなかった証拠」と
みなしてよい）が要らないため、7候補の中で最も実現しやすい。PreToolUseの
`hookSpecificOutput.permissionDecision: "deny"`で実行前制御として成立する
（後述シミュレーションで実際に動作確認済み）。

### 中: spec-first違反の禁止（候補6）

候補5と違い、こちらは「新規schemaファイルを書こうとしている」ことまでは
パスパターンで機械的に検出できるが、「対応するspecが**合意済みか**」は
機械的に判定できない。近似案として「同名のschemaRef文字列を参照する
usecase specファイルが`.waffle/specs`配下に存在するか」をgrepすることは
できるが、これは弱い代理指標に留まる（スタブだけのspecを先に置けば
すり抜けられる・逆に正当な理由で先にschemaを触るケース（バグ修正等）を
誤検知する可能性がある）。「合意済み」という状態を機械的にどう表現するか
（specのstatusフィールド等）が決まらないと、候補6は実装できても
意味のある制御にならない。

### 中: RenderMetaSchema閉じた語彙違反の事前検知（候補7）

チェックロジック自体は`test_agg_schema.py`として既に存在する（実現の土台は
ある）が、これを**PreToolUse**（書き込み前）で使おうとすると、Editツールの
`tool_input`は`old_string`/`new_string`の差分であって書き込み後の全体像
ではないため、フック側で「編集後のファイル内容」を組み立て直す必要があり、
候補1〜5より実装コストが一段上がる。**PostToolUse**（書き込み後に検知）で
妥協するなら候補1〜4と同程度の実現可能性まで下がる（ただし「事前に止める」
という候補7本来の狙いは失われ、事実上候補1〜4寄りの用途1に近づく）。

### 全候補に共通する実現可能性の上限

これら全てはClaude Code Hooks機構への依存が前提であり、
`brainstorm-multitool-loop-goal.md`で扱っているマルチツール対応の論点と
そのまま衝突する。**Claude Code以外のツール（Copilot CLI・Kiro CLI等）は
同等のHooks機構を持つとは限らず、持っていたとしても互換の設定形式では
ない可能性が高い**。したがって「実現可能性が高い」候補であっても、それは
あくまで「Claude Code上でなら」という限定付きである。

---

## シミュレーション（2026-07-12、実際に動かした結果）

「文字だけでは実現可能性の判断ができない」という指摘を受け、候補5（実行前
ブロック）と候補1（自動発火）を実際に動くスクリプトとして書き、実際の
ペイロードを流し込んで動作確認した。**Waffleのdocumentへの本番Hookとして
`.claude/settings.json`には未登録**（あくまで実現可能性検証のための使い捨て
スクリプト）。

### 候補5シミュレーション: document.json直接編集をPreToolUseで拒否する

```python
# protect-document-json.py（PreToolUseフックとして動く想定）
import json, re, sys

payload = json.load(sys.stdin)
file_path = payload.get("tool_input", {}).get("file_path", "")

if re.search(r"\.waffle/documents/.*\.json$", file_path):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"document.json は CLI/MCP 経由（scaffold "
                f"fill / patch-schema）で編集してください。直接Edit/Writeで書き込"
                f"もうとしたパス: {file_path}",
        }
    }, ensure_ascii=False))
sys.exit(0)
```

**ケースA（違反を再現）**: このセッション冒頭で実際に起きた「`uc-patch-schema.json`
を直接Editしようとする」操作を模したPreToolUseペイロードを標準入力から流したところ:

```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": "document.json は CLI/MCP 経由（scaffold fill /
patch-schema）で編集してください。直接Edit/Writeで書き込もうとしたパス:
/home/daidaiiro/workspace/waffle/.waffle/documents/specs/bc-waffle/subdomain/
sd-schema-management/usecase/uc-patch-schema.json"}}
```
→ `permissionDecision: "deny"`が返り、Claude Code側はこのツール呼び出しを
**実行前に**拒否できることを確認した。

**ケースB（正当な操作）**: `tests/unit/domain/test_schema_patch.py`へのEdit
（document.json配下ではない）を同じスクリプトに流したところ、**何も出力せず
exit 0**（=フック側に判断なし＝通常の許可フローに委ねる＝許可される）。
誤検知しないことを確認した。

### 候補1シミュレーション: schema書き込み直後にcheck-schema-version-driftを自動発火する

```python
# trigger-schema-drift-check.py（PostToolUseフックとして動く想定）
import json, re, subprocess, sys, time

payload = json.load(sys.stdin)
file_path = payload.get("tool_input", {}).get("file_path", "")

if re.search(r"src/waffle/domain/model/.*/v\d+\.json$", file_path):
    t0 = time.monotonic()
    result = subprocess.run(
        ["uv", "run", "--project", ".", "waffle", "check-schema-version-drift"],
        cwd="/home/daidaiiro/workspace/waffle", capture_output=True, text=True,
    )
    elapsed = time.monotonic() - t0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
        "additionalContext": f"[Hook] {file_path} への書き込みを検知し "
            f"check-schema-version-drift を自動実行しました（{elapsed:.2f}秒）。"
            f"結果: {result.stdout.strip()}"}}, ensure_ascii=False))
sys.exit(0)
```

`DomainSpecSchema/v5.json`へのWriteを模したPostToolUseペイロードを流したところ:

```
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
"[Hook] .../DomainSpecSchema/v5.json への書き込みを検知し
check-schema-version-drift を自動実行しました（0.14秒）。結果:
{\"broken_references\": [], \"newer_version_available\": [],
\"missing_declared_fields\": []}"}}

real  0m0.161s（Hookスクリプト自体のPythonプロセス起動オーバーヘッド込み）
```
→ フック発火からCLI実行・結果整形までEnd-to-Endで**0.16秒**。セッションの
体感速度に影響しないレベルであることを実測で確認した。

### シミュレーションで分かったこと

- 候補5・候補1とも、想定していたメカニズム（`permissionDecision: deny`での
  実行前ブロック、`additionalContext`でのモデルへの結果フィードバック）が
  **文書通りに動作した**。実現可能性「高」という評価は実測で裏付けられた
- 候補5の「例外なく機械的に判定できる」という主張も、正当な操作（ケースB）で
  誤検知しないことを実際のexit code/出力で確認できた
- 候補1のコスト懸念（デバウンス要否）は、実測0.14〜0.17秒という数字により
  「杞憂だった」と言い切れる根拠ができた
- 候補6・候補7は今回シミュレーションしていない（機械的に「合意済みか」を
  判定するロジック自体が未設計のため、動かして見せられる段階にない）

---

## 再検討: Hookとして「入れるべきか」の判断（2026-07-12）

「実現可能性が高い＝入れるべき」ではない、という指摘を受けて、候補1〜7を
「そもそもHookという手段が適切か」まで踏み込んで再検討した。ここで
前段の実現可能性評価（候補1〜4=高）に**見落としがあった**ことが分かった。

### 見落とし: 候補1・3はEdit/Write起点のHookではほぼ発火しない

候補1（schema版ずれ検知）・候補3（spec参照整合性検知）は「schema/specsへの
書き込み直後」をトリガーに想定していたが、Waffleの規律上これらは**CLI経由
（`patch-schema`/`scaffold fill`）で書くのが正しい書き方**であり、CLIは
Bashツール経由で呼ばれる。つまりEdit/Writeツールを監視するPostToolUse Hook
は、**正常な書き込み経路をそもそも観測できない**（観測できるのは規律違反の
raw Edit/Writeのときだけ）。前段の実現可能性評価は「Edit/Writeで発火させれば
成立する」という前提が誤っていたことになる。

これを踏まえ、候補ごとに「Hookという手段が本質的に必要か」を再判定する。

### 判断基準: CLIをバイパスする経路にのみHookは価値がある

- 書き込みが**Waffle CLI経由で行われる**（document.json/specs/schemaの
  既存編集）→ CLIを呼ぶusecaseコード自身にチェックを組み込める。Hookに
  頼らずとも実現でき、かつHookより移植性が高い（Claude Code依存にならず、
  `brainstorm-multitool-loop-goal.md`が扱うマルチツール対応とも矛盾しない）
- 書き込みが**Waffle CLIを経由しない**（`.py`ソースコードの直接編集、
  または新規schemaファイルの作成のようにCLIの代替経路自体が存在しない場合）
  → Waffle側のコードが関与する余地がなく、**Hookでしか自動化できない**

### 候補ごとの再判定

| # | 候補 | 判定 | 理由 |
|---|---|---|---|
| 5 | document.json直接編集の禁止 | **Go（最優先）** | CLIバイパスの検知そのもの。Hook以外に手段がない。シミュレーション済みで誤検知なし |
| 4 | operation名の実装乖離検知 | **Go** | usecase実装(`.py`)はCLIを介さず直接編集される。Hookでしか自動化できない正当な対象 |
| 2 | シナリオ⇔テスト乖離検知 | **Go（testファイル側のみ）** | testファイルは直接編集される。spec側(TestScenariosブロック)は`scaffold fill`経由なので、そちらは`scaffold_document.py`内部に組み込むべきで、Hookでは拾えない |
| 6 | spec-first違反の禁止 | **条件付きGo** | schema新規作成にはCLIの代替経路が無く、Hookが唯一の手段。「合意済み」の代替指標として、参照specの`status`フィールドを使う案が新たに見つかった（後述） |
| 1 | schema版ずれ検知 | **No（Hookとしては）** | 大半のschema書き込みは`patch-schema` CLI経由。Hookは「raw Editでの例外編集」しか拾えず、本来やりたい「毎回のschema変更後にチェック」にならない。**`patch_schema.py`usecase内部にチェックを組み込む方が正しい** |
| 3 | spec参照整合性検知 | **No（Hookとしては）** | specsはほぼ常にCLI経由。Edit/Write起点のHookはほぼ発火しない。`scaffold`のcreate/fill内部に組み込むべき問題であり、Hook化する理由がない |
| 7 | 閉じた語彙違反の事前検知 | **No** | 既存テストで十分カバー済み。書き込みが`patch-schema`経由である以上、Hookより`patch-schema`内部バリデーションの方が適切 |

### 候補6の改善案: spec.statusを合意済みの代替指標にする

候補6の弱点（「同名のschemaRefを参照するspecが存在するか」だけではスタブで
すり抜けられる）について、`DomainSpecSchema/v5`の`status`フィールドが
`CREATED`/`VALIDATED`/`RENDERED`/`SUPERSEDED`というenumを実際に持っている
ことを確認した（`uc-patch-schema.json`は現に`VALIDATED`）。「同名schemaRefを
参照するspecが存在し、かつそのstatusが`VALIDATED`以上」を条件にすれば、
`scaffold create`しただけの未検証スタブ（`CREATED`止まり）は弾ける。ただし
`VALIDATED`は`waffle validate`が構造的に通ったことを意味するだけで、
「人間が内容に実質的に合意したか」までは保証しない、という限界は残る
（AIが自動生成した内容がそのままvalidateを通ることは有り得るため）。

### 全体の結論

Hooksが本質的に価値を持つのは「CLIをバイパスする経路（raw Edit/Write、
あるいはCLIの代替経路が存在しない新規ファイル作成）でしか発生し得ない問題」
（候補2・4・5・6）だけである。CLIを経由する経路の問題（候補1・3・7）は、
Hookではなく**Waffle自身のusecaseコードにバリデーションとして組み込む方が
正しい層**であり、Hook化を検討する必要自体がない。

---

## 候補6・1・3・7の詳細シミュレーション（2026-07-12）

「何を検知したいのか分からない」という指摘を受け、4候補それぞれについて
「具体的に何を検知したいか」「実際に動かした結果」「入れることの効果」
「適切なタイミング」を個別に整理する。

### 候補6: spec-first違反の禁止

**何を検知したいか:** `.waffle/specs`配下に合意済み（`status`がVALIDATED以上）
のusecase specが存在しない状態で、新しいschemaファイルを書こうとする行為
そのもの。今回実際に起きた「HandoffSchema/v1を無spec状態で実装した」違反が
そのまま検知対象。

**シミュレーション:** 参照schemaRefを持つspecをグロブ検索し、
`status`が`VALIDATED`/`RENDERED`のものが1件でもあれば許可、無ければ拒否する
スクリプトを実際に書いて動かした。

- ケースA（`HandoffSchema/v1`を新規作成）→ **deny**（該当spec 0件）:
  `"HandoffSchema/v1 を新規作成しようとしていますが、これを参照し
  status=VALIDATED以上のusecase specが見つかりません…"`
- ケースB（既存の`DomainSpecSchema/v5`を編集）→ **allow**（該当spec 21件が
  VALIDATED以上）: `"DomainSpecSchema/v5 を参照するVALIDATED以上のspecが
  21件見つかりました。"`

**効果:** 今回の実違反を機械的に再現・遮断できることを確認した。UDD原則を
「言葉で言うだけの規律」から「機構による強制」に格上げできる。

**適切なタイミング:** PreToolUse、`src/waffle/domain/model/**/v*.json`への
**新規**Write時のみ判定（既存schemaの更新は対象外＝候補1・6は判定対象が
「新規作成か既存編集か」で棲み分けられる）。

### 候補1: schema版ずれ検知（Hookとしては機能しない、を実演）

**何を検知したいか:** document.jsonが持つ`schemaRef`が、実在するschema版と
ズレていないか（存在しない版を指す・最新版でない・schema新フィールドに
未追従）。

**シミュレーション:** このセッションで実際に使った`patch-schema`のBash
コマンド（`uv run ... waffle patch-schema --operation set_field ...`）を
`tool_name: "Bash"`のペイロードとして、Edit|Write監視のHookスクリプトに
流したところ、**「matcher=Edit|Writeのためtool_name='Bash'には発火しない」
という結果になり、正規の書き込み経路が素通りすることを実演で確認した**。
対比として、同じファイルへの`raw Edit`（規律違反のケース）を流すと確かに
発火した——つまりこのHookは「正しい使い方をしたときは動かず、違反したときだけ
動く」という、候補1が本来やりたかったこと（every legitimate schema change後の
チェック）とは逆の挙動になる。

**効果（Hookとして）:** 限定的。大半の正規schema編集を見逃す以上、
「schemaが変わるたびdriftを検知する」という目的を達成できない。

**適切なタイミング:** Hookではなく、`patch_schema.py`の`write_text()`直後に
`check_backward_compatible`と同様の内部呼び出しとして組み込むのが正しい。
実測では、CLIを2回（`patch-schema`→`check-schema-version-drift`）
外部プロセスとして直列実行すると0.34秒（`uv run`起動オーバーヘッドが
2重にかかる）。同一プロセス内で呼べばこれより確実に速くなる。

### 候補3: spec参照整合性検知

候補1と同じ理由（specsの書き込みはほぼ全て`scaffold fill`/`create`という
CLI経由であり、Edit/Write監視のHookでは正規の書き込み経路を観測できない）で
Hookとしては機能しない。個別シミュレーションはしていないが、候補1の実演が
そのまま当てはまる。`scaffold_document.py`の`create`/`_fill`直後に内部で
呼ぶべき問題。

### 候補7: 閉じた語彙違反の事前検知

**何を検知したいか:** `x-render`等のRenderMetaSchema閉じた語彙（`paragraph`/
`list`/`table`/`section`/`keyvalue`/`code`/`divider`/`sequence`/
`statediagram`/`kvtable`/`architecture`/`flowchart`）に無い値（タイプミス等）
が書き込まれること。

**シミュレーション:** 実在する`DomainSpecSchema/v5.json`の`SummaryBlock`
（`"as": "list", "from": "items"`）に対する2種のEditペイロードを用意し、
old_string/new_stringから編集後の内容を再構成した上でx-render全体を走査する
スクリプトを実際に動かした。

- ケースA（`"as": "list"` → `"as": "bulletlist"`というタイプミス）→
  違反を検出: `{"path": ".$defs.SummaryBlock.x-render[0].as", "value":
  "bulletlist"}`
- ケースB（`"as": "list"` → `"as": "section"`という閉じた語彙内の正当な変更）
  → 違反なし

**効果:** 検知ロジック自体は正しく動く。実行速度も1ミリ秒未満で、候補1同様
「重くて使い物にならない」という懸念は実測では否定された。

**分かった追加コスト:** ただし候補5・6が「file_pathを正規表現でマッチさせる
だけ」の1ステップで完結するのに対し、候補7は「ファイルを追加で読み込む→
old_string/new_stringを手動適用して再構成→JSON再パース→x-render全走査」の
4ステップが必要で、実装の複雑さが一段上がることを実演で確認した（実行時間は
問題にならないが、コードの複雑さ・「old_stringが最新内容と一致しない」場合の
エラーハンドリングなど、候補5には無かった考慮点が増える）。

**適切なタイミング:** これも本来は`patch-schema`usecase内部で「書き込み前」の
バリデーションとして実装するのが最も筋が良い。usecase自身が「これから
書き込もうとしている完成形」をその時点で保持しているため、Editの差分から
再構成するという候補7特有の余計なステップが不要になる。

---

## 追記: aggregate版のクラス名ドリフト検知が存在しない（2026-07-12）

「Spec・フォルダ構造・実装のクラス名をASTしてドリフト検知するものは含まれて
いますか」という質問をきっかけに、既存のdriftチェックを数え直した。
これまで「4種」と説明してきたが、実際には**5種類目**として
`check-usecase-class-drift`（`src/waffle/application/usecases/
check_usecase_class_drift.py`）が既に存在し、AST（`ast.parse`/`ast.walk`）で
実装ファイルのクラス定義を機械的に抽出し、usecase specが宣言する
`operationName`と一致するかを検証していた。これをHook候補一覧に単純に
数え忘れていたのは記録として訂正する。

### 見つかった空白: aggregateはこの種のドリフト検知対象になっていない

`check_usecase_class_drift.py`は`if doc.get("specKind") != "usecase":
continue`でaggregate specを最初からスキップしている。これはバグではなく、
**aggregateにはusecaseのような「1つの名前＝1つのPythonクラス」という単純な
1:1対応が実装上存在しないため**である。実際に`grep`したところ、`class Schema`
や`class Document`という集約ルート名そのもののクラスは存在しない
（`SchemaRepository`/`DocumentRepository`というPort名はあるが、集約ルート
自体はdomain service関数群・複数usecaseクラスにまたがって実現されている）。

既存の`check-spec-integrity`の`orphaned_value_objects`は一見近いことを
やっているように見えるが、実際には**agg-spec内部の整合性**（そのagg-spec
自身が宣言するEntitiesの属性型とValueObjectsの名前の突き合わせ）でしかなく、
**agg-specの宣言と実際のJSON Schemaファイル（`$defs`）との突き合わせ**は
どこにも存在しない。

| specKind | モデルの実装先 | 既存ドリフト検知 |
|---|---|---|
| usecase | Pythonクラス（AST） | `check-usecase-class-drift`（既存） |
| aggregate | JSON Schemaの`$defs` | **無い**（`orphaned_value_objects`はspec内部だけ） |

### なぜこの非対称が生まれているか（ユーザー指摘、2026-07-12）

usecaseの実装対応をASTで機械的に追えるのは、Waffleのusecase実装が「1操作＝
1クラス」という素直なOOP対応を持っているため。一方aggregateの「モデル」が
Pythonの Entity クラスとして実装されておらず、JSON Schemaの`$defs`ブロック
定義そのものがモデルの実体になっている——これが非対称の直接の原因。

ここでユーザーから、より根本的な指摘があった:

> これ本来はモデルの部分がEntityであるところがJsonSchemaになってるからだろうね。
> これ本来はEntityで定義されるのが本来ですからね。少なくともアーキテクチャを
> 決定するときにフォルダ構造が決まると思いますし、集約やユースケースは
> レイヤーアーキテクチャを採用している以上、domainとapplicationというフォルダ
> 内に入ってくるものだと思ってます。

つまり:
- DDD原則に沿えば、集約（Entity/ValueObjectを持つ一貫性の単位）は本来
  **`domain/`配下の実際のEntityクラス**として実装されるべきものであり、
  JSON Schemaの`$defs`はその代替物に過ぎない、という見方ができる
- レイヤードアーキテクチャを採用している以上、集約は`domain/`、usecaseは
  `application/`というフォルダ配置がアーキテクチャ決定の時点で規定される
  はずであり、この「フォルダ構造」もドリフト検知の対象になり得る
  （`check-usecase-class-drift`は実装ファイルの**存在パス**も
  `missing_implementation_file`として検知しているので、usecase側は既に
  フォルダ構造も検知範囲に含んでいる）

この指摘を踏まえると、「aggregate版のJSON Schema `$defs`突き合わせ検知を
追加する」という当初の発想（既存の非対称をそのまま埋める発想）とは別に、
**「集約がEntityクラスとして実装されていないこと自体がアーキテクチャ上の
ギャップではないか」という、より上流の問い**が浮かび上がった。この場合、
先に埋めるべきは「ドリフト検知の追加」ではなく「集約の実装方針そのもの
（JSON Schemaのままでよいか、Entityクラス化すべきか）」になる可能性がある。

**この論点はHooksの話ではなくなっている。** tech-lead-advisor
（レイヤー境界・依存方向のバックボーンを持つ）とddd-advisor（集約・
ドメインモデルのバックボーンを持つ）に相談すべき設計判断であり、本ブレスト
の範囲を超える。別建ての論点として切り出す必要がある。

---

## 集約Entity化の是非（ddd-advisor・tech-lead-advisor統合見解、2026-07-12）

AgentSchema v2のgoal-dispatch構造で両advisorに並列相談した結果、対立点は無く
方向性は完全に一致した。

### 各意見

- **ddd-advisor**: 現状（集約をJSON Schemaの`$defs`のみで表現しPythonの
  独立したEntityクラスを持たない）は「部分的に許容できるが一部是正すべき
  ギャップ」。Waffleの差別化ロジック（drift検知群）は既にPythonの業務
  サービスとして実装されており妥当。しかしJSON Schemaは構造検証（型・必須・
  パターン）しかできず、集約が本来持つべき「状態を変更できる経路を自分
  自身のメソッドだけに絞る」という不変条件のカプセル化がPython側に存在
  しない点は`domain-model.md`の原則に反するギャップ。判断基準は「不変条件が
  静的構造制約に閉じているか、手続き的ルールを含むか」で、後者のみEntity化
  すべき。正典の方向は**Entityを正典としJSON Schemaをそこから導出する**方が
  原則に整合するとした。
- **tech-lead-advisor**: 「Entityをdomain/に置くこと自体は正しい方向性」と
  しつつ、`architecture-evidence-based-scope`の決定木を適用し、**今この場
  での着手には反対**。理由は「JSON Schemaのみの運用で実際に起きた不具合・
  欠落の実例が示されていない」こと。正典の方向性についてはddd-advisorと
  同じ結論（Entityを正典としJSON Schemaを導出する方が依存方向原則に自然）
  に達しつつ、「実例が1〜2件観測されるまでは現状維持（JSON Schema契約＋
  `check-schema-version-drift`による二重管理監視）が妥当」と明言。

### 統合見解

両者とも「Entityクラスをdomain/に持ち、JSON Schemaはそこから導出される
契約とする」という正典の位置づけ（Pythonが正典、JSON Schemaが投影）で
合意している。違いは「今やるか」の一点のみ：ddd-advisorは判断基準（不変
条件の複雑さで見極める）を示すに留めたのに対し、tech-lead-advisorは
Waffle自身の`architecture-evidence-based-scope`原則（実証された欠落が
無い抽象化は先送りする）を根拠に、明確に「今は着手しない」という結論まで
踏み込んだ。

### 合意事項

- 集約をJSON Schemaの`$defs`のみで表現する現状の設計は、アンチパターンとは
  言えない
- 本来集約が持つべき「不変条件のカプセル化」のうち、静的構造制約に閉じない
  部分（状態遷移・相互依存ルール）はPython側に置き場所が無く、実例が出れば
  是正すべきギャップである
- **今は変換・コード生成の仕組みを作らない**。JSON Schemaを唯一の正典として
  維持し、`check-schema-version-drift`による二重管理監視を継続する
- 着手条件（トリガー）: 「JSON Schemaだけでは防げなかった不変条件違反」
  または「usecase層に同じ判定ロジックが重複し始めた」という具体的な実例が
  1〜2件観測された時点。その際はPythonの集約Entityを正典とし、JSON Schema
  をそこから生成する方向を優先検討する

### 着手条件の再検討・着手を決定（2026-07-12）

上記の「実例待ち」という結論に対し、ユーザーから異なる角度の反論があった。

> 集約Entity化の是非もできることならやりたいよね。アーキテクチャとして
> あるべき形はそれが正しいしね。今回JsonSchemaになったのは、当初の思想が
> かなり大きいです。あとはJsonSchemaというものにすでにバリデーションの
> 機能があり、既存資産の流用がうまくはまったという背景もあるからだけど、
> こと実装においては少しイレギュラーになっているのでここらでちゃんとした
> 設計と実装に是正するのもありかもしれないんで。

tech-lead-advisorの「実例が無いから待つ」という判断基準
（`architecture-evidence-based-scope`）は、「将来のための投機的な抽象化を
先回りして作らない」ことを目的とした原則である。しかし今回の論点は
それとは性質が異なる：**現状のJSON Schema採用は、DDD原則に基づく設計判断
ではなく、「JSON Schemaに既にバリデーション機能があり、既存資産の流用が
うまくはまった」という実装都合で選ばれた経緯があり、それ自体が最初から
筋の通っていない技術的負債だった**、という指摘である。「不具合が起きるまで
待つ」べき投機的拡張ではなく、「最初から正しくなかったものを、気づいた今
是正する」話であるため、evidence-based-scopeの適用対象として同一視すべき
ではない。

この整理に基づき、**集約Entity化に着手することを決定した**。ただし、
実装にいきなり入るのではなく、UDD原則（spec-first）に沿ってまず
`sd-schema-management`配下でusecase specとして設計を固めてから実装に
進める（着手範囲は次回以降のセッションで具体化する）。

### advisor再相談で判明した論点のズレ、および真の動機の確定（2026-07-12）

上記の決定を受け、ddd-advisor・tech-lead-advisorに実データ（agg-schema.json
のInvariants 9件中8件がJSON Schemaで静的検証済み、1件のみ手続き的で既に
`check_backward_compatible()`実装済み）を持って再相談したところ、
**ddd-advisorが「Schema集約についてEntity化は不要」と、前回の着手決定を
覆す結論**を出した（tech-lead-advisorは「Entity化する前提」で移行設計を
返したため、両者の結論が対立した）。

この対立を受けてユーザーに確認したところ、**Entity化を求める本当の動機が
判明した**：ddd-advisorへの相談は「振る舞い・不変条件のカプセル化が必要か」
という問いだったが、ユーザーの実際の関心は**「specと実装のドリフトを機械的に
検知できる構成になっているか」**という、Waffle自身の再現性・冪等性の担保
だった。ddd-advisorが検討していた論点とは別物であり、相談の立て方自体が
ずれていた。

実際に確認したところ、このドリフトは架空の心配ではなく実在した:
`agg-schema.json`は「Schema」Entityが`schemaId`/`version`/`kindProfiles`
という属性を持つと宣言しているが、実際の`AgentSchema/v2.json`にはこれらの
フィールドが文字通り存在しない（`schemaId`+`version`は`$id`という1つの
文字列"AgentSchema/v2"に合成され、`kindProfiles`は`if/then/else`による
discriminator構造として暗黙的に実現されているのみ）。**agg-specが宣言する
形を、実際のschemaファイルが本当に満たしているかを、現状誰も検証していない**。

この時点で「agg-schemaと実schemaファイルをJSON同士で直接突き合わせる軽量な
専用チェック」という代替案（Entity不要、Python言語非依存）を提示したが、
ユーザーはこれを明確に却下した:

> このスキーマファイルのためだけに作る検知ドリフトは本来例外的なので、
> waffleとしてこうする場合は正しくエンティティとして決められた言語で
> 実装することが正しいので、そこを検知できるような仕組みに合わせてほしい

つまり動機は**検知アーキテクチャの統一性**である：`check-usecase-class-drift`
が確立している「spec宣言 → 対応する実コードの成果物が実在するかを検証する」
という一般形を、集約にも同じ形で適用したい。agg-schemaだけの特殊対応
（JSON同士の一点物チェック）は、Schema集約がたまたまJSON Schemaという
JSON形式で表現されているという個別事情に依存した例外であり、他の集約
（Document集約等、JSON同士の比較が成立しない可能性がある）には汎用化
できない。

### 最終的な整理（ddd-advisorとの整合）

ddd-advisorの結論（「複雑な振る舞い・不変条件のカプセル化は不要」）とは
矛盾しない。**振る舞いを持つリッチなEntityである必要はなく、ドリフト検知の
対象になれる薄いクラス（dataclass相当、状態変更メソッドの充実は求めない）
として実在させれば足りる**、という整理に収束した。相談すべきだった問いは
「この集約に複雑な業務ロジックがあるか」ではなく「この集約の構造を、
usecaseと同じ検知パターンで検証可能な形にするには何が要るか」だった。

### 結論・次のアクション

- 集約Entity化に着手する（決定を維持。ただし目的は「DDD的な振る舞いの
  カプセル化」ではなく「`check-usecase-class-drift`と同型のドリフト検知を
  集約にも適用可能にすること」に修正する）
- Entityは薄い構造（属性定義のみ、複雑な業務ロジックメソッドは不要）で
  よい。tech-lead-advisorが示した設計（Entity定義はdomain/、
  Entity→JSON Schema変換はPort/Adapterでアダプター層、段階移行、
  patch-schemaのEntity経由への一本化）はそのまま活用できる
  （振る舞いの複雑さに関する前提が変わっても、レイヤー配置・移行手順の
  設計自体は妥当なため）
- 検知チェック自体（集約版`check-usecase-class-drift`）は、前述の
  言語非依存性の議論（tree-sitter採用）とも合流する：Entity→実装言語への
  対応関係を、Python専用の`ast`ではなくtree-sitterベースのPort/Adapterで
  検証する、という設計が両方の論点に共通して使える
- 次のアクション: `sd-schema-management`配下でこの統一検知アーキテクチャ
  （usecase版・aggregate版が同じ検知パターンに従う）をusecase specとして
  設計する

### Port/Adapter設計の確定（2026-07-12）

ユーザーから最後の確認があった:「もし本格的にやるのであれば、JSON Schemaでの
検知の部分をアダプターに任せるっていうような構成にするのが、アーキテクチャ
的には正しいかもしれません」。これはtech-lead-advisorが既に提案していた
`SchemaProjectorPort`案と、集約版ドリフト検知（言語非依存のクラス名抽出）を
対にする形で確定した。

```
Port: ClassDeclarationExtractor（source, language → クラス名一覧）
  → Adapter: TreeSitterClassExtractor（実装言語側の検知。tree-sitter採用）

Port: SchemaProjector（Entity → JSON Schemaの$defs構造）
  → Adapter: JsonSchemaProjector（JSON Schema形式での投影・検知）
```

コア（ドメイン層の比較ロジック：「specが宣言した属性」と「実際に検出された
構造」を突き合わせる部分）はどちらの技術（tree-sitterかJSON Schemaか）にも
依存せず、技術的詳細は完全にアダプター側に閉じ込められる。これは
architecture-port-adapterの原則（コアは「何が必要か」だけを知り「どう
実現するか」を知るべきではない）に沿った、この一連の議論全体の最終的な
アーキテクチャ形状として確定した。

### 実装フェーズでの矛盾発覚とスコープ確定（2026-07-12・実装完了）

上記のPort/Adapter設計を受けて実装に着手し、以下を完了した:

- `uc-check-aggregate-class-drift`をUDD spec-firstで新設（`sd-reconciliation`
  配下）。`check-usecase-class-drift`と同型の検知パターンを集約に適用
- `src/waffle/domain/entities/schema.py`にSchema Entity（`SchemaId`/`Version`/
  `KindProfile`/`Schema`、いずれも`frozen=True`の薄いdataclass）を実装。
  agg-schema.jsonのEntities/ValueObjects宣言をそのまま仕様として実装した
  （新しいusecase specは不要——agg-schema.json自体が既に集約の仕様であるため）
- 実装の結果、`check-aggregate-class-drift`はagg-schema（Schema集約）の
  ドリフトを検知しなくなり、残るagg-document（Document集約、今回のスコープ外）
  のみを正しく報告する状態になった（全275テスト通過）

この過程で、当初のSchemaProjector設計と矛盾する事実が判明した。今回実装した
Schema Entityは意図的に薄く（`schema_id`/`version`/`kind_profiles`の3属性のみ）
保っているが、実際の`DomainSpecSchema/v5.json`のような本物のJSON Schema
ファイル（各ブロックのproperties・x-render・x-prompt-query等、数百行の詳細）
を、この薄いEntityから再生成することはできない——情報量が根本的に不足している。
ddd-advisorの「薄いEntityでよい」という判断と、tech-lead-advisorの
「Entityを正典としてJSON Schemaを生成する」というSchemaProjector設計は、
実装してみて初めて両立しないことが判明した。

ユーザーに確認した結果、**Entityは薄いまま維持し、JSON Schemaは引き続き
`patch-schema`/`scaffold`経由の手書きを正典とする**方針で確定した。
SchemaProjector（Entity→JSON Schema生成）は作らない。`patch-schema`の
内部一本化（Entity経由への書き込み経路統一）も行わない。

**最終的なEntityの役割:** DDD的な振る舞いのカプセル化のためでも、JSON Schema
生成の正典のためでもなく、**check-aggregate-class-driftというドリフト検知の
対象になるための、最小限の構造的な存在証明**に限定される。JSON Schemaが
唯一の構造検証・レンダリング・scaffold契約であり続ける点は、本ブレスト冒頭の
「Hooksが本質的に価値を持つのはCLIバイパス経路の問題だけ」という結論とも
整合する——Entityも同様に「ドリフト検知という限定された目的のためだけの、
最小限の追加」に留まった。

この論点はここで完了とする。Document集約（agg-document）のEntity化は、
同じパターンを横展開すればよいが、着手は次回以降に判断する。

### 検知の空洞化を実測で発見・修正（2026-07-12）

上記完了報告の直後、ユーザーから「これだと全く意味がない気がする。作らないのと
一緒かもしれない」という指摘があった。実際に検証したところ正しかった:

```python
class Schema:
    pass
```
という**中身が空のクラス**でも、当時の`check-aggregate-class-drift`はクラス名
一致だけを見ていたため検知をすり抜けた。つまりEntity化してもドリフト検知の
実効性はゼロに近かった。

これを修正し、`check-aggregate-class-drift`にクラス名だけでなく**フィールド名
集合の一致**も検証する`attribute_mismatch`を追加した（AST上のクラス本体直下の
`AnnAssign`宣言を抽出し、agg-specのEntities宣言する属性名(camelCase)をsnake_case
変換したものと突き合わせる）。同時に発見した副産物として、camelCase→snake_case
変換ロジックが`operation_name_to_module_name`という usecase固有の名前の関数に
埋もれていたため、`canonical_naming.py`に汎用の`to_snake_case`として切り出し、
既存関数はその薄いラッパーに変更した（振る舞いは変えていない）。

修正後、実際のSchema Entity（`schema_id`/`version`/`kind_profiles`）が
agg-schema.jsonの宣言（`schemaId`/`version`/`kindProfiles`）と正しく一致する
ことを実データで確認済み。spec（`uc-check-aggregate-class-drift`）・実装・
TDDテスト（空クラスがattribute_mismatchで検知されることを含む）を全て更新し、
全276テスト通過・5種のdriftチェック全てクリーンな状態を維持している。

**教訓:** 「ドリフト検知を追加した」という宣言だけでは、検知が実際に機能する
保証にはならない。今回のように「わざと空にしたらすり抜けるか」を実際に試す
（ミューテーションテスト的な視点）ことで、初めて検知の実効性を検証できた。

### ValueObjectsも未検知だった問題を追加修正（2026-07-12）

上記の修正後もユーザーから「JSON Schemaに特化したドリフト検知になっていない
か。本来はEntity・ValueObjects・DomainServiceのクラス名乖離を検知したい」と
いう指摘があり、確認したところ**ValueObjectsが一切検証対象になっていなかった**
ことが判明した（`agg-schema.json`が宣言する`SchemaId`/`Version`/`KindProfile`
が実装から消えても検知できない状態だった）。

これを修正し、`check-aggregate-class-drift`に`missing_value_object`を追加した
（ValueObjectsが宣言する各名前が、集約ルートと同じ実装ファイル内のクラス定義
名として存在するかを検証。フィールドまでは見ず、クラスの実在のみ）。
spec・実装・TDDテスト（値オブジェクトが欠落した場合を検知するケースを含む）を
更新し、全277テスト通過・5種のdriftチェック全てクリーンな状態を維持している。
実データでも`SchemaId`/`Version`/`KindProfile`が正しく検知対象になることを
確認済み。

### 今回のスコープ外として明示的に切り分けた論点（2026-07-12）

同じ指摘の中でユーザーから、以下がずっと「もやもやしていた」懸案として
語られた。いずれも設計判断・スコープが大きいため、**今回は着手せず、次回
以降の論点として明示的に記録する**（実装をなし崩し的に広げることを避ける
ため）。

1. **KindProfileと実際のJSON Schemaファイルの紐付け**: 「EntityにはKindProfile
   を持っているが、そのProfileに紐づくのがそれぞれの定義しているJSON Schema
   になるような実装になると想定していた」という発言があった。現状の
   `KindProfile`ValueObjectは`name`と`required_blocks`しか持たず、実際の
   `AgentSchema/v2.json`・`CodingSchema/v2.json`等の実ファイルへの参照を
   一切持たない（インスタンス化もされていない、定義だけの空の構造）。
   これをどう繋ぐか（KindProfileが実schemaファイルへのパスを持つのか、
   別の対応表を持つのか）は未設計
2. **Document集約のEntity化**: 「document集約もあるけど、実際のアーキテクチャ
   になぞるとEntityがあるはず」という指摘。Schema集約と同じパターンを
   横展開すれば機械的にはできるが、着手は次回以降に判断する

### 論点2の深掘り: 「能動的Entity」か「受動的Entity」か（2026-07-22）

「実際にDocument集約を置いた場合、どのような使われ方をするか」という問いを
受けて検討した。現状`document_loading.py`の`load_document()`は生dictを返し、
`query_document.py`/`render_document.py`/`validate_document.py`/
`scaffold_document.py`/`patch_schema.py`は全てこの生dictを直接操作している。
Document Entityの置き方には2つの道がある:

1. **受動的**（Schema集約と同じ）: ドリフト検知の対象になるためだけの薄い
   存在。実行パスには一切登場しない
2. **能動的**: `load_document()`が実際に`Document`インスタンスを構築し、
   以降の全usecaseがdictではなく`Document`オブジェクトを操作するよう
   書き換える。application層のほぼ全体に触れる大改修になる

最初「適しているか」という観点で受動的を推奨したが、ユーザーから
「都合ではなくアーキテクチャとして正しい方」を問われ、`agg-document.json`の
Invariants実データ（7件中6件が`enforcement: "guard"`——状態遷移・終端状態・
横断的ガード等の手続き的ルール）を確認した。これはSchema集約（9件中8件が
`enforcement: "schema"`）と真逆の分布であり、一見「複雑な業務ロジック→
リッチなEntityクラスが必要」という結論に見えた。

しかし実際のコードを確認したところ、**この判断は既にコードベース自身に
よって下されていた**ことが判明した。`lifecycle_guard.py`のdocstring:

> JSON Schema は構造/値の検証はできるが状態遷移は表現できないため、
> 遷移表そのものは schema に宣言的データ（x-lifecycle）として持ち、
> この関数はそれを読むだけの薄い executor（**imperative な集約クラスは
> 持たない**）。

6件のguard系不変条件は、既に`lifecycle_guard.py`（状態遷移）・
`schema_ref_guard.py`（schemaRef必須）という純粋関数のドメインサービスとして
実装済みで、複数usecaseから呼ばれている。「imperativeな集約クラスは持たない」
は明記された設計判断であり、思いつきではない。

**確定した結論:** DDD原則として正しいのは「複雑な手続き的ロジック→リッチな
Entityクラス」だけではなく、「複雑な手続き的ロジック→ドメインサービス
（状態を持たない純粋関数）」という`business-logic-simple.md`のもう1つの
パターンでもある。Waffleは`check_backward_compatible`・`operation_drift.py`・
`scenario_drift.py`・`lifecycle_guard.py`・`schema_ref_guard.py`と、既に
一貫してこちらを採用している。したがってDocument集約も**受動的Entity＋
既存のドメインサービス関数群**が、都合ではなくアーキテクチャとして正しい
選択となる（Schema集約と結論は同じだが、根拠が「面倒だから」ではなく
「Waffle全体の既存の一貫したパターンに従うべきだから」という点が異なる）。

3. **DomainServicesのドリフト検知**: 前述の通り、DomainServicesはaggregate
   specではなくsubdomain specに属し、かつ宣言が日本語の業務語彙（例:
   「後方互換チェック」）でありコード識別子（PascalCase等）を持たない。
   usecaseの`operationName`のような専用フィールドをDomainServicesBlockに
   追加するschema変更が前提になる、より大きな設計判断

### 論点3の深掘り: 汎用性とファイル単位検知の妥当性（2026-07-22）

Entity/ValueObjectの検知（クラス名＋フィールド名の突き合わせ）とDomainService
の検知（当初「関数名」を想定）の汎用性（Python/Java/TypeScript/JavaScript
という初期対象OOP言語群への適用可能性）を検討した。

- **Entity/ValueObject**: 「クラスがフィールドを持つ」という概念は4言語
  共通のため、抽出部分をtree-sitterベースのPort/Adapterに差し替えれば
  （既に確定した方針のまま）検知ロジック自体は変更不要で汎用的に成立する
- **DomainService**: 「モジュールレベル関数」というPythonの流儀は
  Python/TypeScript/JavaScriptでは自然だが、**Javaには存在しない概念**
  （必ずstatic methodかサービスクラスに押し込む必要がある）。「関数名を
  検知する」という設計のままでは汎用的に成立しない。着手時は
  `ClassDeclarationExtractor`だけでなく、関数/メソッド単位も扱える
  もう一段広い抽象化（`CodeArtifactExtractor`相当）が必要になる

さらに、ユーザーから「サービスはそれごとにファイルを作成するはずだから、
ファイル名でドリフト検知できるのでは」という代替案が出たため、実データで
検証した。`sd-schema-management.json`が宣言する2つの業務サービス
「後方互換チェック」「契約整形」は、**両方とも`schema_patch.py`という
同じ1ファイルに同居**していた（一方`sd-document-management.json`の3サービス
はおおむね1ファイル1サービスで対応していた）。つまり**1サービス＝1ファイル
という規約は徹底されておらず、ファイル名ベースの検知案は成立しない**
ことが実証された。

**やる価値はあるか:** Yes。「後方互換チェック」と「契約整形」が同じファイルに
無自覚に同居している状態そのものが、今回のセッションの教訓（宣言と実装の
対応関係を機械的に見ていないと気づけない）の実例になっている。

### 論点3の設計確定: serviceName + fileNameの2フィールド、ファイル存在確認のみ（2026-07-22）

当初「関数名までASTで突き合わせるべきか」を検討したが（実際に
`check_backward_compatible`関数だけを消してもファイル存在チェックでは
気づけないことを実演で示した）、ユーザーから「中身が空でもすり抜けるは
あり得ない。そこはTDDでテストシナリオが落ちるので検知できる」という
指摘があり、これは正しいと判断した。

**TDDとdriftチェックの守備範囲の違いを整理:**
- TDD（既存のacceptance/unit test）が担保するもの: 実装の**振る舞いが
  壊れていないか**（関数が削除・破壊されればテストが即座に落ちる）
- driftチェックが担保すべきもの: spec宣言と実装コードの**名前の対応関係**
  が保たれているか（usecaseのケースで言う「リネームの片方だけ反映し
  忘れる」）。振る舞いの正しさとは別の関心事

この2つは別の関心事であり、後者はファイルの存在確認だけで十分カバーできる
（関数レベルの内容破壊はTDDが別途担保するため、driftチェック側で二重に
見る必要はない）。

**確定した設計:** `DomainServicesBlock`に`serviceName`（PascalCase、例:
`CheckBackwardCompatible`）と`fileName`（例: `schema_patch`）の2フィールドを
追加する。1ファイルに複数サービスが同居することを許容し（`schema_patch.py`
の実例に合わせる）、検知は「宣言されたfileNameのファイルが実在するか」の
存在確認のみに留める。usecase/aggregateの`class_name_mismatch`/
`attribute_mismatch`のような関数名・シグネチャレベルの突き合わせは、
言語非依存性の複雑さ（`CodeArtifactExtractor`相当の抽象化）とTDDとの
守備範囲重複を踏まえ、あえて作らない。

---

## 追記: ドリフト検知アルゴリズムは言語非依存でなければならない（2026-07-12）

上記の議論とは別に、ユーザーから重要な制約の指摘があった。

> ただこれを用意しておくメリットはSpecと実装のドリフトを検知できることに
> あるんですよね。これは再現性と冪等性を担保するうえで必要なことだとも
> 感じてます。JsonSchemaでは汎用的な検知ができないのであれば考え物です。
> あとこの検知ですが、言語を問わないようなアルゴリズムであることは注意
> してください。そうなってないとwaffleのコンセプトからずれるので。

### 既存実装内に既に矛盾があった

実際にコードを確認したところ、既存の5種類のdriftチェックの中に既にこの
矛盾が存在していた。

| チェック | 実装方式 | 言語依存性 |
|---|---|---|
| `check-usecase-class-drift` | `import ast; ast.parse(source)` | **Python専用**（他言語のソースは解析不能） |
| `check-operation-drift` | `re.compile(r'operation\s*==\s*"([a-zA-Z_]+)"')` | 正規表現ベース、言語への依存が緩やか |

`CodingSchema`が「アーキ/スタック非依存」を謳っているWaffleのコンセプトに
対し、`check-usecase-class-drift`はPython標準ライブラリの`ast`モジュールに
依存しており、他言語プロジェクトにWaffleを導入した場合は機能しない
（Waffle自身がPythonで実装されているため自己適用する分には動くが、それは
たまたま一致しているだけ）。

### スコープの確認: 初期対象は「オブジェクト指向言語」

ユーザーから対象言語のスコープが明確化された:「waffleを使用して開発する
言語は初期はPythonやJava、TypeScript、JavaScriptのようなオブジェクト指向の
言語を対象にしています」。これにより「あらゆる言語」ではなく「classキーワード
でクラス宣言を持つ主要OOP言語4種」に絞られる。

**シミュレーション:** 4言語共通の正規表現`\bclass\s+([A-Za-z_][A-Za-z0-9_]*)`
を実際に4言語のクラス宣言サンプル（Python/Java/TypeScript/JavaScript、
ジェネリクス込み）に適用したところ、全て正しくクラス名を抽出できた
（`class QueryDocument` → `["QueryDocument"]`、Javaの`class Repository<T>
extends BaseRepo<T>` → `["Repository"]`等）。一方、コメント内の`class`や
文字列リテラル内の`class`にも誤反応する弱点も確認した（`check-operation-drift`
が既に持つのと同種のトレードオフ）。

### 結論（初版）

集約Entity化の議論（着手はしない、実例待ち）とは独立に、**将来ドリフト
検知を拡張する際は`ast`のような言語固有パーサーではなく、正規表現ベースの
言語非依存アルゴリズムを採用すべき**という設計原則が明確になった。これは
`check-usecase-class-drift`（既存）自体が本来是正すべき対象であることも
意味するが、今回のブレストの範囲では実装しない（着手条件は上記の集約
Entity化の議論と同じトリガーに従う）。

### 結論（更新: tree-sitterの採用を決定、実装は先送り、2026-07-12）

正規表現案には「コメント・文字列リテラル内の`class`にも誤反応する」という
精度の弱点があったため、実在するライブラリを調査した結果、
**tree-sitter**（多言語対応のインクリメンタルパーサー）が要件に合致すると
分かった。PyPIに`tree-sitter-python`/`tree-sitter-java`/
`tree-sitter-typescript`/`tree-sitter-javascript`という言語別グラマー
パッケージが個別に存在し（`tree-sitter-language-pack`という306言語を
まとめたパッケージも2026-07-02公開で存在する）、各言語グラマーとも同じ
クエリAPI（S式クエリ、例: `(class_declaration name: (identifier) @name)`）
でクラス宣言を抽出できる。コメント・文字列リテラルとコードを構文的に区別
できるため、正規表現案の弱点を解消できる。

**Port/Adapterでの設計方針（決定・実装は先送り）:**
```
Port:    ClassDeclarationExtractor（source, language → クラス名一覧）
Adapter: TreeSitterClassExtractor（言語ごとのtree-sitterグラマーを使い分け）
```
`check_usecase_class_drift.py`側の比較ロジック（spec宣言 vs 実装クラス名の
突き合わせ）は変更不要。既存specの記述（「実装クラスが実際に持つクラス名」）
はPython/ASTを明示的に前提としていないため、この乗り換えはspecの内容変更を
伴わない純粋な内部実装の入れ替えとして扱える。

**実装タイミングの判断:** tech-lead-advisorが集約Entity化の文脈で示した
`architecture-evidence-based-scope`原則（実証された欠落・実例に基づいて
機能追加すべき）は、この乗り換えにも同様に当てはまる——現状Waffleが検証
対象にしているのは自分自身のPython実装のみで、実際に他言語プロジェクトへ
Waffleを導入してこの検知が必要になった実例はまだ無い。そのためユーザーとの
確認の結果、**設計方針（tree-sitter採用・Port/Adapter化）はここで確定させ
つつ、実装そのものは他言語プロジェクトへの導入等の実例が出た時点まで
先送りする**ことにした。着手条件は集約Entity化の議論と同じトリガーに従う。

---

## 未検討

- 用途1（drift自動発火）と用途2（実行前制御）を同一の機能として設計するか、
  別々のusecaseとして分離するか
- Waffle自身がHooks機構を持つのか、既存ツール（Claude Code Hooks等）への
  設定生成・連携に留めるのか
- 用途2（実行前制御）は原理的にWaffle側のコードだけでは実現できず、
  呼び出し元ツール側のHooks機構との連携が必須になる可能性がある
  （Waffleはあくまで呼ばれる側のCLI/MCPであり、呼び出しを遮る主体になれない）
- どのイベント（書き込み直後・セッション終了時・定期実行）を対象にするか

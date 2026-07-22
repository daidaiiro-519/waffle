# ブレインストーミング: drift-check系usecaseのパス解決を、architecture文書から動的に導出する

**目的:** `check-usecase-class-drift`等のdrift-check系usecaseが`srcRoot`等のパスをCLIオプションのデフォルト値としてWaffle自身のパス（`src/waffle/application/usecases`等）にハードコードしている問題を解消し、Waffleを使う任意のプロジェクト（言語・アーキテクチャを問わず）で同じdrift検知が機能するようにする。
**モード:** 問題解決

---

## 問題の再定義

drift-check系usecase（`check-usecase-class-drift`・`check-operation-drift`・`check-domain-service-drht`・`check-aggregate-class-drift`）が、実装ファイルの配置場所（`srcRoot`）をCLIオプションのデフォルト値としてWaffle自身のディレクトリ構成にハードコードしているせいで、他プロジェクトがWaffleを使って開発する際に、そのプロジェクト自身のarchitecture文書が宣言する実際の配置（`conceptPlacement`）と実行時のパス解決が連動しない。

## 原因候補

- **表面的原因**: CLIオプション（例: `--srcRoot`のデフォルト値）が`src/waffle/application/usecases`のようにWaffle自身のパスに固定されている
- **根本原因**: architecture文書の`conceptPlacement`（概念→配置の宣言）を実行時に読んでパスを導出する仕組みがそもそも存在しない。`conceptPlacement`は人間・AIが読むための説明文としてのみ存在し、コード内を全文検索しても一度もプログラムから参照されていないことを確認済み

---

## 論点 1: パスの動的解決は、どこで・どうやって行うべきか

### AI 初期見解
**見解:** `.waffle/config.json`（既に`toolMappings`等を持つ、プロジェクト単位の設定ファイル）に「このプロジェクトの現在の対象architecture文書はどれか」を指す1つの参照（例: `codingProduct: "waffle"`）を追加し、drift-check系usecaseはCLIオプションのデフォルト値としてハードコードする代わりに、この参照から`architecture-{codingProduct}.json`を読み、`conceptPlacement`の該当concept（例: `usecase`）の`placement`値を`srcRoot`として導出する設計にすべきだと考える。

**根拠:**
- `.waffle/config.json`は既に「このプロジェクト固有の、実行時に参照する設定」を持つ場所として確立している（`toolMappings`が既にその実績）。新しい設定の置き場所を増やさずに済む
- `conceptPlacement`は既にDomainSpecSchemaのusecase等が持つ`concept`のキー名（"usecase"等）と一致させる規約になっており（x-prompt-write参照）、drift-check側が`concept: "usecase"`で該当行を検索する対応関係は既存の宣言規約とそのまま噛み合う
- `init-coding-preset`（今回実装したプリセット機構）で生成された`architecture-{product}.json`が、まさにこの動的解決の入力になる。プリセット機構と組み合わさることで、「initした瞬間から、そのプロジェクトのdrift検知が言語非依存に機能する」という一貫した体験になる

**ただし未解決の懸念:**
- `layout.tree`（正典ディレクトリツリー全体を示す自由文字列）と`conceptPlacement.items[].placement`（個々の概念の相対パス）の関係が今は非構造化（`layout.tree`はテキストで人間が読むためのツリー図であり、`{package}`のようなプレースホルダを含む自由文字列）。`srcRoot`を機械的に導出するには、`placement`が指す相対パスの起点（`src/{package}/`部分）をどう補うかが未決着
- 複数言語（Python実装のusecaseとTypeScript実装のusecase等）が同一プロジェクトに混在する場合、`codingProduct`という単一の参照だけで済むのか、それとも対象ファイルの拡張子から使うべきarchitecture文書を都度選ぶ必要があるのかも未検討

### ユーザー見解
> 「実現しやすい方法は？」「src/{package}の階層って一般的です？」という問いかけを通じ、
> 実際にpython-hexagonal/typescript-hexagonalプリセットの中身を確認させた。
> 最終的な訂正案（`layout.sourceRoot`新設＋`path_template.resolve`再利用）には「良さそう」と合意。

### AI 再考見解
**見解:** 「`{package}`を置換すれば済む」という初期の実現案は、Python版プリセットの`layout.tree`が
たまたま`src/{package}/`という形だったことに引きずられた誤りだった。実際に両プリセットを
確認した結果、TypeScript版は`src/`のみで`{package}`階層自体を持たない（1リポジトリ=1パッケージ
が普通なので不要）ことを確認した。訂正案: `LayoutBlock`に新規フィールド`sourceRoot`を追加し、
各プリセットが自分の言語の慣習に合った値を持つ（python版: `"src/{package}"`、ts版: `"src"`）。
実行時は`sourceRoot + "/" + conceptPlacement.placement`を組み立て、既存の`path_template.resolve()`
（scaffold_document.pyが既に使う汎用トークン置換）にそのまま渡す。`{package}`という特定トークンを
特別扱いする専用ロジックは書かず、無ければ素通りするだけの汎用置換に任せる。

**根拠:**
- 実際に2プリセットの`layout.tree`を突き合わせて確認したことで、「一般的だと思い込んでいた
  構造が実は1言語の慣習に過ぎなかった」という事実誤認を実装前に発見できた
- 新設フィールドは1つ（`LayoutBlock.sourceRoot`）のみ、既存の`conceptPlacement.placement`・
  `path_template.resolve`は変更不要で再利用できるため、実現コストは小さいまま維持できる

### 合意決定
**決定:** `LayoutBlock`に`sourceRoot`フィールドを新設し、`sourceRoot + "/" + conceptPlacement.placement`
を`path_template.resolve()`へ渡す形でdrift-check系usecaseのパスを動的解決する。
**理由:** 既存フィールド・既存の汎用トークン置換を最大限再利用しつつ、Python/TypeScriptで
実際に異なるディレクトリ慣習（`{package}`階層の有無）を正しく吸収できる、実現コストの低い設計。
**次のアクション:** 前回の反省（spec-firstの手順違反）を踏まえ、実装に入る前に
ddd-advisor/tech-lead-advisorへ敵対的検証を依頼し、その後CodingSchema/v3への`sourceRoot`
フィールド追加、2プリセットへの値追加、drift-check系4usecase（check-usecase-class-drift・
check-operation-drift・check-domain-service-drift・check-aggregate-class-drift）への
動的解決ロジック追加を、正式なusecase spec（既存specの変更として扱う）をVALIDATEDにしてから
実装する。

---

## 実施状況（2026-07-22・完了）

前回の反省（spec-first手順違反）を踏まえ、今回は実装コードを1行も書く前に
spec/schema/handoffを確定させた:

1. **spec/schema/handoff先行コミット**（commit `8bf0690`）: CodingSchema/v3→v4作成、
   `LayoutBlock.sourceRoot`追加（treeとの整合ガイダンスも追記）、既存8文書のv4移行、
   architecture-waffle/architecture-typescript-hexagonalへの`sourceRoot`バックフィル、
   `bc-waffle.json`への`ResolveConceptSourceRoot`業務サービス宣言追加、
   `handoff-concept-source-root-resolution.json`作成。この時点で`check-domain-service-drift`が
   未実装ファイルを正しく検知することを確認（spec-firstが本来機能している状態の実演）
2. **実装**（commit `6fb5d4a`）: `concept_source_root.py`（新規ドメインサービス、単体テスト6件）、
   CLI（4コマンド）・MCPアダプター両方に`--architectureRef`対応を追加（MCPには同種の
   ハードコード問題が独立して存在しており、実装中に発見して同時に修正）。
   全518テストパス、全drift-checkクリーン
3. **副産物の発見**: 実装検証の過程で、`architecture-waffle.json`の`conceptPlacement`/`layout.tree`が
   実態と食い違っていた（aggregate/entity/value-objectの配置を"domain/model"と宣言していたが、
   実際の実装クラスは"domain/entities"にあった。domain/model/はWaffle成長の過程でschema JSON
   定義の置き場に転用され、DDD実装クラスの置き場ではなくなっていた）ことを発見し、同じコミットで
   修正した。動的解決を実際に実装・実行したことで初めて可視化されたドリフトであり、
   「ハードコードされたデフォルト値が正しい記述を裏付けている」という誤った安心感を
   生んでいたことの実例になった。

**次のアクション:** 無し。この一連の作業は完了。
# 宣言された部品の種別ごとに、成果物の形を決める：ds-render-parts

## 概要

- Schemaが宣言する描画の指定とDocumentの中身の両方を読み、部品の種別ごとに決まった形へ整えて成果物を組み立てる計算。

---

## 存在意義

- この計算はSchemaの宣言とDocumentの中身の両方を同時に読む。どちらか一方の集約の内側へ置くと、もう一方を集約の外から読むことになり、境界が意味を失う。
- 整え方はDocumentの状態を変えない。読んだ結果から成果物を組み立てるだけで、不変条件を守る責任を持たない——だから強い一貫性が要らず、集約の外に置ける。
- 同じ整え方を、描画の入口（成果物の生成・雛形の描画・ビューアの生成）が共有する。入口ごとに持たせると、同じ宣言から違う形が出る。

---

## 参照する集約

| 集約 | 触れ方 | 何のために |
|---|---|---|
| agg-document | 参照のみ | 整える対象は Document の中身である。 |
| agg-schema | 参照のみ | 部品の種別と整え方の指定は Schema の宣言から得る。 |

---

## 入力と出力

### 受け取るもの

| 名前 | 意味 |
|---|---|
| 描画の指定 | Schemaのブロックが宣言する、部品の種別と、その種別ごとの整え方の指定。 |
| 描画の対象 | Documentのcontentのうち、その指定が指す値。 |

### 返すもの

| 名前 | 意味 |
|---|---|
| 整えられた成果物の一部 | 宣言された種別の整え方に従って組み立てた、成果物の断片。 |

### 決められない入力

- 宣言された部品の種別が、描画の語彙に無いとき
- 指定が配列を要する部品なのに、指す値が配列でないとき

---

## 受け入れ基準

| 基準 |
|---|
| When ブロックが部品の種別を宣言しているとき、この計算はその種別に定められた整え方だけを使って形を決める shall（種別ごとの整え方を呼ぶ側が選べると、同じ宣言から違う形が出る）。 |
| When 同じ宣言と同じ中身を繰り返し与えたとき、この計算は常に同じ形を返す shall。 |
| While 形を決める間、この計算はSchemaもDocumentも書き換えない shall（読むだけの計算であり、状態を持たない）。 |
| If 宣言された部品の種別が描画の語彙に無いとき、この計算は形を決められない shall（呼ぶ側がエラーとして扱う）。 |

---

## 受け入れシナリオ

### paragraph・listが正しく整形される

| 分類 | 観点 |
|---|---|
| 正常系 | paragraph/listの整形保証 |

```gherkin
Scenario: paragraph・listが正しく整形される
  Given paragraph/listを宣言するx-render
  When renderする
  Then paragraphは地の文、listは箇条書きとして整形される
```

### tableはパイプ文字をエスケープしboolを整形する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのセルエスケープ・bool整形保証 |

```gherkin
Scenario: tableはパイプ文字をエスケープしboolを整形する
  Given パイプ文字やbool値を含む行データ
  When tableとしてrenderする
  Then パイプ文字はエスケープされ、boolは✓/-に整形される
```

### sectionは入れ子とitemLabelを整形する

| 分類 | 観点 |
|---|---|
| 正常系 | sectionの入れ子・itemLabel整形保証 |

```gherkin
Scenario: sectionは入れ子とitemLabelを整形する
  Given itemLabelを持つsection宣言と入れ子のeach部品
  When renderする
  Then 各itemの見出しにitemLabelが付与され、入れ子の部品も正しく描画される
```

### keyvalueが正しく整形される

| 分類 | 観点 |
|---|---|
| 正常系 | keyvalueの整形保証 |

```gherkin
Scenario: keyvalueが正しく整形される
  Given keyvalueを宣言するx-render
  When renderする
  Then ラベルと値の組が箇条書きとして整形される
```

### sectionはbadgeで条件付き強調を付与する

| 分類 | 観点 |
|---|---|
| 境界値 | sectionのbadge（条件付き強調）保証 |

```gherkin
Scenario: sectionはbadgeで条件付き強調を付与する
  Given badge条件を満たすitemを含むsection宣言
  When renderする
  Then 条件を満たすitemの見出しにのみ強調語が付与される
```

### tableはmarkFieldで識別子を太字強調する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのmarkField（識別子強調）保証 |

```gherkin
Scenario: tableはmarkFieldで識別子を太字強調する
  Given markFieldが真の行を含むtable宣言
  When renderする
  Then 該当セルが太字＋markSuffixで強調される
```

### statediagramが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | statediagramのMermaid構文生成保証 |

```gherkin
Scenario: statediagramが正しいMermaid構文になる
  Given 状態遷移の配列を宣言するx-render
  When renderする
  Then stateDiagram-v2として正しいMermaid構文が生成される
```

### statediagramは疑似状態を表現する

| 分類 | 観点 |
|---|---|
| 境界値 | statediagramの疑似状態（choice/fork/join）保証 |

```gherkin
Scenario: statediagramは疑似状態を表現する
  Given pseudoStatesFromで疑似状態を宣言するx-render
  When renderする
  Then choice/fork/joinの疑似状態宣言がMermaid構文の先頭に出力される
```

### sequenceはactor・participantを区別する

| 分類 | 観点 |
|---|---|
| 境界値 | sequenceのactor/participant区別保証 |

```gherkin
Scenario: sequenceはactor・participantを区別する
  Given kind:actor/participantを含む参加者宣言
  When renderする
  Then actor/participantそれぞれの宣言がMermaid構文で区別される
```

### sequenceはloop・altを入れ子で表現する

| 分類 | 観点 |
|---|---|
| 正常系 | sequenceのloop/alt入れ子保証 |

```gherkin
Scenario: sequenceはloop・altを入れ子で表現する
  Given loop/alt種別のstepを含むsteps配列
  When renderする
  Then loop/altブロックが正しく入れ子のMermaid構文になる
```

### sequenceはactivate・deactivateを表現する

| 分類 | 観点 |
|---|---|
| 境界値 | sequenceのactivate/deactivate保証 |

```gherkin
Scenario: sequenceはactivate・deactivateを表現する
  Given activate/deactivateフラグを持つstep
  When renderする
  Then Mermaidのアクティベーション記法(+/-)が正しく付与される
```

### architectureが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | architectureのMermaid構文生成保証 |

```gherkin
Scenario: architectureが正しいMermaid構文になる
  Given zones/connectionsを宣言するx-render
  When renderする
  Then architecture-betaとして正しいMermaid構文が生成される
```

### flowchartが正しいMermaid構文になる

| 分類 | 観点 |
|---|---|
| 正常系 | flowchartのMermaid構文生成保証 |

```gherkin
Scenario: flowchartが正しいMermaid構文になる
  Given stages/transitionsを宣言するx-render
  When renderする
  Then flowchart LRとして正しいMermaid構文が生成される
```

### kvtableは単一行として整形される

| 分類 | 観点 |
|---|---|
| 境界値 | kvtableの単一行整形保証 |

```gherkin
Scenario: kvtableは単一行として整形される
  Given kvtableを宣言するx-render
  When renderする
  Then block自身の値が1行のtableとして整形される
```

### tableはjoin指定で配列セルを結合整形する

| 分類 | 観点 |
|---|---|
| 境界値 | tableのjoin（配列セル結合）保証 |

```gherkin
Scenario: tableはjoin指定で配列セルを結合整形する
  Given join/sepを指定したcolumns宣言と配列値を持つセル
  When renderする
  Then 配列の各要素がjoinテンプレートで整形されsepで連結される
```

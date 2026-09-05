---
name: design-structured-html
description: Transform dense, scattered, or complex information into a self-contained, cognitively accessible HTML artifact with clear hierarchy, appropriate cards/tables/flows/callouts, semantic markup, and responsive styling. Use when the user asks to organize research, specifications, plans, comparisons, procedures, study notes, reports, or mixed source material into a readable HTML page; when an existing HTML artifact needs structural or visual improvement; or when both human and AI readability matter. 「情報を整理してHTMLに」「カード形式でまとめて」「認知しやすい構造に」「既存HTMLを読みやすく改善して」などの依頼にも使用する。
---

# Design Structured HTML

複雑な情報を、装飾ではなく情報構造から設計した単体HTMLへ変換する。

## 成果物の必須条件

- 最重要メッセージを冒頭で把握できるようにする。
- 情報の性質に合う表現を選び、すべてを同じカードへ押し込まない。
- 見出し、表、リスト、`section`、安定したIDを使い、意味をHTMLに残す。
- 人間向けの視覚階層とAI向けの明示的な意味構造を両立する。
- 外部依存のない単体HTMLを既定とし、レスポンシブ・ダークモード・印刷に対応する。
- 根拠、未確定事項、制約、限界を結論と区別する。

## ワークフロー

### 1. 入力を読み、制約を固定する

すべての入力ファイルを精読する。既存HTMLを更新する場合は、内容だけでなく配色、コンポーネント、用語、セクション順、操作も抽出する。ユーザーが指定した正本、凍結条件、引用、ファイル名、言語を維持する。

### 2. 表示前に意味モデルを作る

次を短く内部整理する。

- 読者と読後にできるべきこと
- 中心となる問い・結論・判断
- 主張、根拠、例外、未確定事項
- 比較、順序、階層、因果、対応関係
- 用語、識別子、出典

文書の骨格選択では [information-architecture.md](references/information-architecture.md) を読む。

### 3. 情報ごとに表現形式を選ぶ

[representation-selection.md](references/representation-selection.md) を読み、読者の課題に合う形式を割り当てる。原則として、正確な対応は表、順序はフェーズまたはフロー、独立概念はカード、重要な境界はCallout、長い補足は`details`を使う。

図やチャートは、関係が文章や小さな表より明確になる場合だけ使う。単純な一段階や少数の事実を図にしない。

### 4. HTMLを組み立てる

新規作成では、必要に応じてテンプレートを初期化する。

```bash
python3 scripts/new_artifact.py output.html --title "文書タイトル" --lang ja
```

テンプレートは完成形ではなく部品集として扱う。入力に不要なサンプルセクションと部品は削除し、内容に適した順序へ組み替える。既存HTMLの編集では、その視覚言語を優先し、全面置換が必要な理由がなければ継承する。

### 5. 視覚言語を一貫させる

[visual-language.md](references/visual-language.md) を読む。色には文書内で安定した意味を割り当てる。色だけで意味を伝えず、ラベル、見出し、アイコン相当の文字情報を併用する。余白、角丸、境界線、影、文字サイズの種類を増やしすぎない。

### 6. 人間とAIの読み取りを確認する

[semantic-html.md](references/semantic-html.md) を読む。関連する定義・根拠・測定方法・例外を近接させ、各セクションを可能な範囲で自己完結させる。同じ概念には同じ表記とIDを使う。重要情報をJavaScript実行後だけ表示したり、画像・Canvas・CSS疑似要素だけに持たせたりしない。

### 7. 操作を最小限に追加する

長い文書には目次、現在位置、スクロール進捗、テーマ切替を追加できる。コードや構造化データにはコピーボタンを追加できる。操作は閲覧を補助するものに限定し、本文へのアクセスをJavaScriptに依存させない。

### 8. 検証する

構文・意味構造を検証する。

```bash
python3 scripts/validate_artifact.py output.html
```

図を含む成果物は、**提示する前に必ず実際に描画し、その画像を読み返して目で確認する**。手で座標を書いたSVGは、描くまで崩れているかどうかが分からない。座標が数値として正しく見えることと、絵として成立していることは別である。

```bash
uv run --no-project --with resvg-py --with fonttools \
    python3 scripts/render_svg_check.py output.html --out-dir <一時ディレクトリ>
```

出力されたPNGを1枚ずつ開いて見る。スクリプトが報告するのは規則として書ける崩れ（枠からのはみ出し、囲みを跨ぐ要素、囲みの辺への密着、文字が描かれなかったこと）だけであり、線と文字の衝突、詰まりすぎ、そもそも図として伝わらないことは画像を見ないと分からない。崩れを直したら、描き直して再び見る。崩れが無いことを画像で確認するまで提示しない。

続いて実ブラウザまたは利用可能なプレビューで、デスクトップ幅とモバイル幅を確認する。最低限、横方向のはみ出し、表のスクロール、目次リンク、テーマ、印刷、長い日本語、コードブロックを確認する。検証環境がなければ、その制約を明記して静的検証結果を提示する。

## 品質判断

- 冒頭だけで「何の文書か・何が重要か・次に何を見ればよいか」が分かるか。
- 各セクションが一つの主要な問いに答えているか。
- 主張と根拠、変数と取得方法、判断と条件が近くにあるか。
- 比較対象の粒度と列の意味が揃っているか。
- カードを外しても見出し階層だけで文書構造が理解できるか。
- 色を見なくても意味が伝わるか。
- 文書をテキスト抽出しても順序と関係が保たれるか。
- 装飾が内容より目立っていないか。

## 禁止事項

- 内容を理解する前にテンプレートへ流し込まない。
- カード、グラデーション、色、バッジを密度目的で乱用しない。
- 同じ内容を要約、表、カードで無意味に三重化しない。
- 正確な値の照合を装飾的なグラフだけで表さない。
- 重要な注意を色だけ、ホバーだけ、折りたたみの中だけで示さない。
- 出典や確度が異なる情報を同じ断定表現で混ぜない。

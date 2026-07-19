# 同梱書体（自己完結アセット層）

商用級モックを**外部依存ゼロ**で出すために、ライセンス上再配布可能な書体を Latin subset の woff2 で同梱している。
生成HTMLの `@font-face` に `url(FONT:<name>)` マーカーを書き、`scripts/embed_fonts.py` で data URI へ埋め込む（ランタイム依存は python3 のみ）。

## 収録フェイス

| name（FONT:マーカー） | 実体 | 用途 | ライセンス |
|---|---|---|---|
| `lato-400` | Lato Regular | 本文・UI | SIL OFL 1.1（`Lato-OFL-copyright.txt`） |
| `lato-700` | Lato Bold | 見出し・強調 | 同上 |
| `lato-900` | Lato Black | 屋号/大見出し・メトリクス値 | 同上 |
| `dejavu-mono-400` | DejaVu Sans Mono | データ列・数値（tabular） | Bitstream Vera/DejaVu（`DejaVu-license.txt`） |

いずれも Latin＋Latin-1＋Latin Ext-A＋句読点＋矢印＋幾何記号にサブセット済み（各16〜38KB）。
Lato は humanist sans で「安全だが無難」＝それ自体は個性の源泉ではない。**個性はウェイト対比・字間・題材データ・形の符号化で作る**（書体を入れれば商用になるわけではない）。

## 使い方
1. モックの `@font-face` に `src:url(FONT:lato-400) format('woff2')` 等を書く。
2. `python3 scripts/embed_fonts.py <mock.html>` で data URI 化（自己完結HTMLになる）。

## 日本語・ブランド書体・別フェイスが要るとき
- 同梱は Latin 中心。**日本語や顧客ブランド書体は「顧客提供」**（value-prop: 内蔵アセット＋顧客提供のみ）。
- 提供された ttf/otf を**そのモックで使う文字だけにサブセット**して woff2 化する準備手順（`fonttools`+`brotli` が必要。ランタイムでなく準備時のみ）:
  ```
  python3 -m venv env && ./env/bin/pip install fonttools brotli
  ./env/bin/pyftsubset <font.ttf> --text-file=<mockの可視テキスト> --flavor=woff2 \
      --output-file=assets/fonts/<name>.woff2 --layout-features='*' --no-hinting
  ```
  日本語は全グリフだとMB級なので、**使う文字だけのサブセットが必須**（fonttoolsが無い環境では埋め込みを諦め、システムフォントスタックにフォールバックする）。

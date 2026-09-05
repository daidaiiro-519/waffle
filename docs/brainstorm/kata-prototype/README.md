# Kata 原型 ── ブレストの論点を試すために作ったもの

`docs/brainstorm/brainstorm-schema-conception-three-tiers.md` の議論で、
**主張を口で言わずに確かめるために作った使い捨ての原型。** Waffle の実装ではない。

## これは何を確かめたか

| ファイル | 役 |
|---|---|
| **`core.py`（167行）** | **中核層。プロファイルの意味を1つも持たない。** これが本体 |
| `migrate.py`（48行） | 版の移行。閉じた操作集合を宣言順に当てる |
| `p/ddd.json` ・ `p/research.json` | プロファイル2つ。**中核層は両方を知らない** |
| `p/*.md.json` | 変換契約。**テンプレートはコードではなくデータ** |
| `instance/` | 実体2つ（予約ドメイン／`spec-correspondence` の章立て） |
| `schema/ddd@1,2.json` ・ `migration-*.json` | 版の移行を試すための材料 |
| `src/reservation.py` | 突き合わせの相手。ドックストリングに名乗りを書いてある |
| `render/` | 射影の出力（MD 2版・HTML） |
| `tok/` | 形式ごとのトークンを測るのに使った同一内容の4ファイル |
| `kata.py` ・ `contracts.py` | **旧版。`core.py` に置き換わった。** 契約に DDD が漏れていたのを直す前の姿として残してある |

## 分かったこと

- **正規化と射影の冪等は成立した。** 鍵順を逆にし、濁点を NFD 分解し、`null` の欄を足した別表現から、同じ正規形・同じ出力が出る。100回射影してバイト列が一致する
- **名前を鍵にすると壊れる。** 節を別の親へ移すと差分が `removed 1 / added 1` になる。不変の印を鍵にすると `moved 1` になり、突き合わせの件数が前後で変わらない。スキーマの版を上げても同じ
- **「中核層は意味を持たない」は、2つ目のプロファイルを書くまで嘘だった。** 契約のコードに種別の名前が直に入っていた。契約を Python からデータへ移して初めて消えた
- **条件つきの問い合わせは、語彙をプロファイルから生成すれば宣言のまま持てる。** 生成したツール定義は 250 トークン
- **HTML への射影は、最初は入れ子になっていなかった。** それではアドレスが DOM の位置を表せない

## 動かし方

```
python3 -c "
import sys; sys.path.insert(0,'.')
import core, json
from pathlib import Path
p = core.Profile('p/research.json'); c = core.Contract('p/research.md.json')
root = json.loads(Path('instance/ST-spec-correspondence.json').read_text())
print(core.render_doc(p, c, root))
"
```

トークンを測る部分だけ `tiktoken` を要る。それ以外は標準ライブラリで動く。

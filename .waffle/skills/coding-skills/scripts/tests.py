"""scripts の振る舞いを確かめる。

  python3 tests.py

`check.py` は文言の照合しかしないので、振る舞いはここで確かめる。
**守るのは主に「静かに素通りする経路」である。**

実際に起きたこと（2026-09-06）── 3つとも、検査は通ったうえで何も見ていなかった。
  ・ 出典の URL を `<small>` で探していて、78行すべてを素通りした
  ・ 規則の ID をハイフンの数で判定し、表の1列目の `JSON` を規則と数えた

外部の依存を持たない ── `README.md` が「ディレクトリ1つで完結し、
Waffle も外部の依存も要らない」と宣言しているためである。
"""
from __future__ import annotations

import re
import subprocess
import sys as _sys
import unittest

import check
from _common import Spec, kinds_by_shape, sections, tables


def spec(body: str, layer="lang.rust", kind="failure") -> Spec:
    from _common import CONSTRAINTS
    return Spec(path=CONSTRAINTS / layer / f"{kind}.md", body=body)


SRC = """
## 規則一覧

| ID | 規則 | 水準 |
|---|---|---|
| RS-ERR-01 | 失敗は値で返す | 必須 |

## 出典

| ID | 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|---|
| RS-ERR-01 | 規格 | Rust Book<br>https://example.test/a | 2026-01-01 取得 | `recoverable` |
"""


class 表を列名で読む(unittest.TestCase):

    def test_ヘッダから列名を取り_行を辞書にする(self):
        tb = tables(SRC)[0]
        self.assertEqual(tb.columns, ["ID", "規則", "水準"])
        self.assertEqual(tb.rows[0]["ID"], "RS-ERR-01")

    def test_列数の合わない行は表に含めない(self):
        body = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 |\n"
        self.assertEqual(len(tables(body)[0].rows), 1)

    def test_区切り行の無い並びは表として読まない(self):
        self.assertEqual(tables("| A | B |\n| 1 | 2 |\n"), [])


class 規則のID(unittest.TestCase):
    """ID の形に依存しない ── `ID` 列に在るかどうかだけで決まる。"""

    def test_出典の表のIDは規則として数えない(self):
        self.assertEqual(spec(SRC).rule_ids, ["RS-ERR-01"])

    def test_ハイフンを持たないIDも規則として拾う(self):
        body = SRC.replace("RS-ERR-01", "N14")
        self.assertEqual(spec(body).rule_ids, ["N14"])

    def test_ID列を持たない表の1列目は規則ではない(self):
        body = """
## 採用するツール

| ツール | 用途 |
|---|---|
| JSON | 直列化 |

## 出典

| 種類 | 原典 | 版・取得日 | 何を裏づけるか |
|---|---|---|---|
| 規格 | x<br>https://example.test/a | 2026-01-01 取得 | `x` |
"""
        self.assertEqual(spec(body).rule_ids, [])


class 写しを持たない(unittest.TestCase):

    def test_層の形ごとの種類はfile_catalogから読む(self):
        by_shape = kinds_by_shape()
        self.assertIn("言語", by_shape)
        self.assertIn("style", by_shape["言語"])
        self.assertIn("layers", by_shape["アーキテクチャ"])


class 検査が宣言を持つ(unittest.TestCase):
    """検査を足すには、守っている宣言が実在しなければならない。"""

    def test_すべての検査が宣言を持ち_その文字列が実在する(self):
        self.assertEqual(check.verify_contracts(), [])

    def test_宣言の無い検査を足すと走る前に止まる(self):
        c = check.Check("架空の検査", "constraints",
                        "references/glossary.md", "この文はどこにも無い", lambda s: [])
        check.CHECKS.append(c)
        try:
            broken = check.verify_contracts()
            self.assertTrue(any("架空の検査" in b for b in broken))
        finally:
            check.CHECKS.remove(c)

    def test_宣言のファイルが無ければ止まる(self):
        c = check.Check("架空の検査", "constraints",
                        "references/nowhere.md", "x", lambda s: [])
        check.CHECKS.append(c)
        try:
            self.assertTrue(any("nowhere.md" in b for b in check.verify_contracts()))
        finally:
            check.CHECKS.remove(c)

    def test_対象は保守するものだけである(self):
        self.assertEqual({c.target for c in check.CHECKS},
                         {"constraints", "references", "templates"})


class 節に切る(unittest.TestCase):

    def test_見出しで切る(self):
        self.assertEqual(list(sections("## あ\nx\n## い\ny\n")), ["あ", "い"])


class 正本が通る(unittest.TestCase):

    def test_いまの規約集は食い違いを持たない(self):
        self.assertEqual(check.main(), 0)



# ══════════════════════════════════════════════════════════════
# ここから下は、宣言から洗い出した振る舞いである。
# 実装を読まずに書き、落ちることを見てから実装を直す。
# ══════════════════════════════════════════════════════════════

from _common import ROOT


def collect(*args):
    r = subprocess.run([_sys.executable, "collect.py", *args],
                       cwd=ROOT / "scripts", capture_output=True, text=True)
    return r.returncode, r.stdout


class 集める(unittest.TestCase):
    """SKILL.md Step 2「軸が一致したものだけが入る」
    「0件の欄があれば、そう表示される」／ Step 4「足りない → 書かずに止める」"""

    def test_軸が一致した規約だけが入る(self):
        _, out = collect("--lang", "rust", "--purpose", "hook")
        self.assertIn("lang.rust/", out)
        self.assertNotIn("lang.go/", out)

    def test_用途の規約が指定した軸が解決される(self):
        _, out = collect("--lang", "rust", "--purpose", "hook")
        self.assertIn("architecture = data-port", out)

    def test_足りなければ終了コード1で止まる(self):
        code, out = collect("--lang", "python", "--purpose", "hook")
        self.assertEqual(code, 1)
        self.assertIn("lang.python", out)

    def test_0件の層も0件として名指しされる(self):
        _, out = collect("--lang", "python", "--purpose", "hook")
        self.assertIn("lang.python/　規約 0 本", out)

    def test_揃っていれば終了コード0(self):
        code, _ = collect("--lang", "rust", "--purpose", "hook")
        self.assertEqual(code, 0)


class 規則が検証方法を持つ(unittest.TestCase):
    """authoring.md Step 5「検証方法を決める」
    ── 機械なら走らせる命令、人なら何を見るかを書く。空欄は検証方法ではない。"""

    def test_規則の各行が水準と検証方法を持つ(self):
        from _common import load_all
        missing = []
        for s in load_all():
            for tb in tables(sections(s.body).get("規則一覧", "")):
                if not tb.has("ID", "水準", "検証方法"):
                    continue
                for row in tb.rows:
                    if not row["水準"].strip() or not row["検証方法"].strip():
                        missing.append(f"{s.where}: {row['ID']}")
        self.assertEqual(missing, [])


class 出典が版を持つ(unittest.TestCase):
    """sources.md「規格｜版と、何を裏づけるか」「原典｜落とした日と、何を裏づけるか」"""

    def test_出典の行の版取得日が空でない(self):
        from _common import load_all
        empty = []
        for s in load_all():
            for tb in tables(sections(s.body).get("出典", "")):
                if not tb.has("版・取得日"):
                    continue
                for row in tb.rows:
                    if not row["版・取得日"].strip():
                        empty.append(s.where)
        self.assertEqual(empty, [])

    def test_版取得日が日付の形をしている(self):
        from _common import load_all
        bad = []
        for s in load_all():
            for tb in tables(sections(s.body).get("出典", "")):
                if not tb.has("版・取得日"):
                    continue
                for row in tb.rows:
                    if not re.match(r"^\d{4}-\d{2}-\d{2} 取得$", row["版・取得日"].strip()):
                        bad.append(f"{s.where}: {row['版・取得日']}")
        self.assertEqual(bad, [])


class 一覧は詳細から導く(unittest.TestCase):
    """一覧を手で書くと、詳細と食い違う。実際に105件中36件で食い違っていた。"""

    BODY = """
## 規則一覧

| ID | 規則 | 水準 | 適用範囲 |
|---|---|---|---|
| RS-ERR-01 | 手で書いた古い言明 | 推奨 | 全体 |

## 規則の詳細

### RS-ERR-01　失敗は値で返す

| 項目 | 内容 |
|---|---|
| 水準 | 必須 |
| 適用範囲 | 公開する関数 |
| 検証方法 | `cargo clippy` |

## 出典
"""

    def test_詳細から一覧の表を組める(self):
        import relist
        got = relist.table_for(spec(self.BODY, kind="failure"))
        self.assertIn("| RS-ERR-01 | 失敗は値で返す | 必須 | 公開する関数 |", got)

    def test_手で書いた一覧との食い違いを見つける(self):
        import relist
        s = spec(self.BODY, kind="failure")
        self.assertIsNotNone(relist.apply(s, relist.table_for(s)))

    def test_一致していれば書き直さない(self):
        import relist
        s = spec(self.BODY, kind="failure")
        fixed = spec(relist.apply(s, relist.table_for(s)), kind="failure")
        self.assertIsNone(relist.apply(fixed, relist.table_for(fixed)))

    def test_見出し行を欄として拾わない(self):
        import relist
        _, _, fields = relist.details(self.BODY)[0]
        self.assertNotIn("項目", fields)

    def test_正本の一覧が詳細と一致している(self):
        import relist
        from _common import load_all
        bad = [s.where for s in load_all()
               if relist.table_for(s) and relist.apply(s, relist.table_for(s))]
        self.assertEqual(bad, [])

class 列名の表記ゆれ(unittest.TestCase):
    """表はヘッダ行で列名を宣言する。空白の違いで列が消えてはならない。"""

    def test_全角空白の入ったヘッダでも列名を取れる(self):
        body = "|　ID　|　種類　|\n|---|---|\n| A-B-01 | 規格 |\n"
        self.assertEqual(tables(body)[0].columns, ["ID", "種類"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

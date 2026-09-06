# -*- coding: utf-8 -*-
"""check_writing.py の振る舞いを、事例で確かめる。

**この検査の失敗は、見えないところで起きる。**
だから確かめるのは、出ることだけではない ──
**出てはいけない場所で出ないこと**と、**どの単位にも当たらない範囲が無いこと**を、
同じ重さで確かめる。

  python3 test_check_writing.py
"""
import os
import tempfile
import unittest

import check_writing as cw


def doc(text):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "a.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def names(text, check=None):
    """その文書で出た検査の名前を並べる。check を渡すとその件数を返す。"""
    f = cw.inspect(doc(text))
    if check is None:
        return [x.check for x in f]
    return [x for x in f if x.check == check]


class 単位に切る(unittest.TestCase):
    def kinds(self, text):
        return [u.kind for u in cw.split_units(text)]

    def test_見出し_本文_箇条書き_引用_表を見分ける(self):
        got = self.kinds("# 見出し\n\n本文である。\n\n- 箇条書き\n\n> 引用\n\n| a | b |\n|---|---|\n| c | d |\n")
        self.assertIn("見出し", got)
        self.assertIn("本文", got)
        self.assertIn("箇条書き", got)
        self.assertIn("引用", got)
        self.assertIn("表のセル", got)

    def test_表の行はセルごとの単位になる(self):
        us = [u for u in cw.split_units("| あ | い | う |\n") if u.kind == "表のセル"]
        self.assertEqual(len(us), 3)

    def test_表の区切り行は単位にしない(self):
        us = cw.split_units("| a | b |\n|---|---|\n")
        self.assertTrue(all("---" not in u.text for u in us))

    def test_字下げされたコードブロックも囲いとして数える(self):
        us = cw.split_units("- 手順\n\n  ```\n  ┌─┐\n  ```\n")
        self.assertIn("コード", [u.kind for u in us])

    def test_フロントマターを単位にしない(self):
        us = cw.split_units("---\nname: x\n---\n\n本文である。\n")
        self.assertNotIn("name: x", [u.text for u in us])

    def test_行番号を保つ(self):
        us = cw.split_units("1行目である。\n\n3行目である。\n")
        self.assertEqual([u.line for u in us if u.kind == "本文"], [1, 3])


class 描画の壊れは_どの単位でも出る(unittest.TestCase):
    """**54%が黙って外れていた原因は、ここだった。**"""

    def 出るか(self, text):
        return bool(names(text, "強調が描画されない"))

    def test_本文で出る(self):
        self.assertTrue(self.出るか("本文である。**壊れた強調。**続き\n"))

    def test_見出しで出る(self):
        self.assertTrue(self.出るか("# 見出しである。**壊れた強調。**続き\n"))

    def test_箇条書きで出る(self):
        self.assertTrue(self.出るか("- 箇条書きである。**壊れた強調。**続き\n"))

    def test_引用で出る(self):
        self.assertTrue(self.出るか("> 引用である。**壊れた強調。**続き\n"))

    def test_コードブロックの中では出ない(self):
        self.assertFalse(self.出るか("```\n本文である。**壊れた強調。**続き\n```\n"))

    def test_表のセルでも_同じ行で1回しか出ない(self):
        hits = names("| 本文である。**壊れた強調。**続き | ふつう | もう1つ |\n",
                     "強調が描画されない")
        self.assertEqual(len(hits), 1)


class 体言止めは_名詞句が自然な単位では出ない(unittest.TestCase):
    def 出るか(self, text):
        return bool(names(text, "体言止め"))

    def test_本文では出る(self):
        self.assertTrue(self.出るか("これは調査結果の記録。\n"))

    def test_見出しでは出ない(self):
        self.assertFalse(self.出るか("# これは調査結果の記録。\n"))

    def test_表のセルでは出ない(self):
        self.assertFalse(self.出るか("| これは調査結果の記録。 | ふつう |\n"))

    def test_箇条書きでは出ない(self):
        self.assertFalse(self.出るか("- これは調査結果の記録。\n"))

    def test_述語で終われば出ない(self):
        self.assertFalse(self.出るか("これは調査の結果を記録したものである。\n"))


class 名詞の連結は_どこでも出る(unittest.TestCase):
    def test_本文で出る(self):
        self.assertTrue(names("設計判断相談材料収集を行う。\n", "名詞を連ねている"))

    def test_見出しで出る(self):
        self.assertTrue(names("# 設計判断相談材料収集\n", "名詞を連ねている"))

    def test_定着した複合語は出ない(self):
        cw.KNOWN_TERMS = {"設計判断相談材料収集"}
        try:
            self.assertFalse(names("設計判断相談材料収集を行う。\n", "名詞を連ねている"))
        finally:
            cw.KNOWN_TERMS = set()


class ASCIIの罫線は_コードの中でも外でも出る(unittest.TestCase):
    def test_コードブロックの中で出る(self):
        self.assertTrue(names("```\n┌──┐\n└──┘\n```\n", "ASCII で図を描いている"))

    def test_字下げされたコードブロックの中でも出る(self):
        self.assertTrue(names("- 手順\n\n  ```\n  ┌──┐\n  ```\n", "ASCII で図を描いている"))

    def test_本文にあっても出る(self):
        self.assertTrue(names("図である。┌──┐ である。\n", "ASCII で図を描いている"))

    def test_二倍ダッシュは図ではない(self):
        self.assertFalse(names("名前と理由を残す ── 消すと、気づけない。\n", "ASCII で図を描いている"))

    def test_木構造は図ではない(self):
        t = "```\nsrc/\n├── a.py\n│   └── b.py\n└── c.py\n```\n"
        self.assertFalse(names(t, "ASCII で図を描いている"))

    def test_横罫が4つ以上続けば図である(self):
        self.assertTrue(names("区切り ──── である。\n", "ASCII で図を描いている"))

    def test_文字で描いた表は図である(self):
        self.assertTrue(names("```\n┬───┬\n```\n", "ASCII で図を描いている"))


class 一文の長さは_散文だけを測る(unittest.TestCase):
    def 出るか(self, text):
        return bool(names(text, "1文が長い"))

    def test_本文の長い文では出る(self):
        self.assertTrue(self.出るか("あ" * 70 + "である。\n"))

    def test_箇条書きでは出ない(self):
        self.assertFalse(self.出るか("- " + "あ" * 70 + "である。\n"))

    def test_表のセルでは出ない(self):
        self.assertFalse(self.出るか("| " + "あ" * 70 + "である。 |\n"))


class 文書全体で見る検査(unittest.TestCase):
    def test_同じ文が2か所にあれば出る(self):
        t = "これは十四文字以上ある長い文である。\n\n別の文。\n\nこれは十四文字以上ある長い文である。\n"
        self.assertTrue(names(t, "同じ文が2か所にある"))

    def test_表の中の同じ文は数えない(self):
        t = "| これは十四文字以上ある長い文である。 |\n\n| これは十四文字以上ある長い文である。 |\n"
        self.assertFalse(names(t, "同じ文が2か所にある"))

    def test_語の対が両方あれば出る(self):
        cw.SYNONYM_PAIRS = [("性質", "特徴")]
        try:
            self.assertTrue(names("性質を見る。特徴を見る。\n", "語の揺れ"))
        finally:
            cw.SYNONYM_PAIRS = []

    def test_借用語があれば出る(self):
        cw.FIGURES = ["当たり判定"]
        try:
            self.assertTrue(names("当たり判定を決める。\n", "別の分野から借りた語"))
        finally:
            cw.FIGURES = []


class 検査そのものの規律(unittest.TestCase):
    """**概念を持たない検査は置かない。**それを機械で確かめる。"""

    def test_すべての検査が概念を持つ(self):
        for c in cw.all_checks():
            self.assertTrue(c.concept, f"{c.name} に概念が無い")

    def test_すべての検査が出方を持つ(self):
        for c in cw.all_checks():
            self.assertIn(c.level, ("指摘", "確認"), f"{c.name} の出方が不正")

    def test_単位に当てる検査は_当てる種別を持つ(self):
        for c in cw.all_checks():
            if c.kinds is not None:
                self.assertTrue(c.kinds, f"{c.name} に当てる種別が無い")
                self.assertTrue(c.kinds <= cw.KINDS, f"{c.name} に知らない種別がある")

    def test_検査を列挙できる(self):
        self.assertGreaterEqual(len(cw.all_checks()), 7)


class 検査から外す印(unittest.TestCase):
    def test_印のある文書は検査しない(self):
        t = "<!-- writing-guard: exempt -->\n\n本文である。**壊れた強調。**続き\n"
        self.assertEqual(names(t), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

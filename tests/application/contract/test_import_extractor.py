"""ImportExtractor portの契約テスト。

仕様のシナリオには対応しない、規約由来のテスト。
言語ごとの構文差はアダプタが吸収し、コアには参照文字列の一覧という
言語非依存の形だけが返ることを確かめる。
"""
import pytest

from waffle.adapters.outbound.tree_sitter_import_extractor import TreeSitterImportExtractor
from waffle.application.ports.import_extractor import UnsupportedLanguage

SAMPLES = {
    "python": ("from probe.domain.order import Order\nimport probe.shared.result\n",
               ["probe.domain.order", "probe.shared.result"]),
    "java": ("import com.example.domain.Order;\n", ["com.example.domain.Order"]),
    "typescript": ("import { Order } from '../domain/order';\n", ["../domain/order"]),
    "javascript": ("import { Order } from '../domain/order.js';\n", ["../domain/order.js"]),
    "go": ('import (\n  "example.com/app/domain"\n)\n', ["example.com/app/domain"]),
    "rust": ("use crate::domain::order::Order;\n", ["crate::domain::order::Order"]),
    "csharp": ("using Example.Domain;\n", ["Example.Domain"]),
    "kotlin": ("import com.example.domain.Order\n", ["com.example.domain.Order"]),
}


def _extractor() -> TreeSitterImportExtractor:
    return TreeSitterImportExtractor()


@pytest.mark.parametrize("language", sorted(SAMPLES))
def test_declared_dependencies_are_extracted(language):
    """宣言された依存の参照を、書かれたまま出現順で返す。"""
    source, expected = SAMPLES[language]
    assert _extractor().imports(source, language) == expected


def test_dependencies_are_returned_in_source_order():
    """複数の書き方が混ざっても、ソース上の出現順で返る。

    クエリの結果は種類ごとにまとまって返るため、並べ直しが要る。
    """
    source = ("import probe.shared.result\n"
              "from probe.domain.order import Order\n"
              "import probe.application.publish\n")
    assert _extractor().imports(source, "python") == [
        "probe.shared.result", "probe.domain.order", "probe.application.publish"]


def test_commonjs_require_is_extracted():
    """require による依存も拾う（import構文ではなく関数呼び出しのため別扱い）。"""
    source = "const order = require('../domain/order');\n"
    assert _extractor().imports(source, "javascript") == ["../domain/order"]


def test_file_without_dependencies_returns_empty():
    """依存を持たないソースには空を返す（エラーにしない）。"""
    assert _extractor().imports("x = 1\n", "python") == []


def test_unsupported_language_is_rejected():
    """対応していない言語は UnsupportedLanguage を送出する。"""
    with pytest.raises(UnsupportedLanguage):
        _extractor().imports("", "cobol")

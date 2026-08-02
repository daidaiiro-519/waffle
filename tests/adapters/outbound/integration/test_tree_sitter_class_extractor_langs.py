"""追加した4言語で、型名とフィールド名を取り出せることのテスト。

仕様のシナリオには対応しない、規約由来のテスト。
言語ごとの構文木の違いは adapter が吸収し、コアは構文解析技術を知らない。
"""
import pytest

from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor

GO = '''
type Order struct {
	Status string
	total  int
}

type Shipment struct {
	Id string
}
'''

RUST = '''
pub struct Order {
    pub status: String,
    total: i64,
}

pub struct Shipment {
    id: String,
}
'''

CSHARP = '''
public class Order {
    public string Status;
    private int total;
}

public class Shipment {
    public string Id;
}
'''

KOTLIN = '''
class Order {
    val status: String = ""
    private val total: Int = 0
}

class Shipment {
    val id: String = ""
}
'''


def _extractor() -> TreeSitterClassExtractor:
    return TreeSitterClassExtractor()


@pytest.mark.parametrize("language,source", [
    ("go", GO), ("rust", RUST), ("csharp", CSHARP), ("kotlin", KOTLIN),
])
def test_class_names_are_extracted_in_order(language, source):
    """宣言された型名を出現順で返す。"""
    assert _extractor().class_names(source, language) == ["Order", "Shipment"]


@pytest.mark.parametrize("language,source", [
    ("go", GO), ("rust", RUST), ("csharp", CSHARP), ("kotlin", KOTLIN),
])
def test_field_names_are_scoped_to_the_class(language, source):
    """指定した型のフィールド名だけを出現順で返す。

    可視性の違い（公開・非公開）で取りこぼさないことも同時に確かめる。
    Goは先頭の大小文字、Rustは pub、C#/Kotlinは修飾子で表す。
    """
    names = _extractor().field_names(source, language, "Order")
    assert [n.lower() for n in names] == ["status", "total"]


@pytest.mark.parametrize("language", ["go", "rust", "csharp", "kotlin"])
def test_field_names_of_unknown_class_is_empty(language):
    """存在しない型名に対しては空リストを返す。"""
    assert _extractor().field_names(GO, "go", "NoSuch") == []

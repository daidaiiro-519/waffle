"""TreeSitterClassExtractor（ClassDeclarationExtractor portのtree-sitter実装）の
ネイティブテスト。Python/Java/TypeScript/JavaScriptの4言語で、クラス名・
フィールド名抽出が正しく機械的に行えることを検証する。
"""
import pytest

from waffle.adapters.outbound.tree_sitter_class_extractor import TreeSitterClassExtractor

_PYTHON_SRC = """
class Schema:
    schema_id: str
    version: str

class Other:
    x: int
"""

_JAVA_SRC = """
public class Schema {
    private String schemaId;
    private String version;
}
class Other { int x; }
"""

_TYPESCRIPT_SRC = """
class Schema {
  schemaId: string;
  version: string;
}
class Other { x: number; }
"""

_JAVASCRIPT_SRC = """
class Schema {
  schemaId;
  version;
}
class Other { x; }
"""


def _extractor() -> TreeSitterClassExtractor:
    return TreeSitterClassExtractor()


@pytest.mark.parametrize("language,source", [
    ("python", _PYTHON_SRC),
    ("java", _JAVA_SRC),
    ("typescript", _TYPESCRIPT_SRC),
    ("javascript", _JAVASCRIPT_SRC),
])
def test_class_namesは全クラス名を出現順で返す(language, source):
    """
    Given 4言語(Python/Java/TypeScript/JavaScript)いずれかのソース
    When class_namesを実行する
    Then 定義されている全クラス名が出現順で返る
    """
    names = _extractor().class_names(source, language)
    assert names == ["Schema", "Other"]


@pytest.mark.parametrize("language,source,expected", [
    ("python", _PYTHON_SRC, ["schema_id", "version"]),
    ("java", _JAVA_SRC, ["schemaId", "version"]),
    ("typescript", _TYPESCRIPT_SRC, ["schemaId", "version"]),
    ("javascript", _JAVASCRIPT_SRC, ["schemaId", "version"]),
])
def test_field_namesは指定クラスのフィールド名を出現順で返す(language, source, expected):
    """
    Given 4言語いずれかのソースと対象クラス名Schema
    When field_namesを実行する
    Then Schemaクラスのフィールド名が出現順で返る
    """
    fields = _extractor().field_names(source, language, "Schema")
    assert fields == expected


def test_field_namesは存在しないクラス名に対して空リストを返す():
    """
    Given ソース内に存在しないクラス名
    When field_namesを実行する
    Then 空リストが返る
    """
    fields = _extractor().field_names(_PYTHON_SRC, "python", "NoSuchClass")
    assert fields == []


def test_class_namesはサポート外の言語を拒否する():
    """
    Given サポート対象外の言語識別子
    When class_namesを実行する
    Then ValueErrorが送出される
    """
    with pytest.raises(ValueError):
        _extractor().class_names(_PYTHON_SRC, "ruby")

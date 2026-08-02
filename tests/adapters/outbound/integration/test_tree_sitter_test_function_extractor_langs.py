"""追加した4言語で、テスト関数と文書コメントを取り出せることのテスト。

仕様のシナリオには対応しない、規約由来のテスト。
突き合わせのキーは文書コメントに置いた宣言行なので、言語ごとに
「どれがテストか」と「文書コメントがどこにあるか」を adapter が吸収する。
"""
import pytest

from waffle.adapters.outbound.tree_sitter_test_function_extractor import (
    TreeSitterTestFunctionExtractor,
)

DECLARATION = "Scenario: 支払い済みなら発送できる"

GO = f'''
// {DECLARATION}
// Given 支払い済みの注文
func TestOrderCanShip(t *testing.T) {{
}}

// これはテストではない
func helper() {{
}}
'''

RUST = f'''
#[cfg(test)]
mod tests {{
    /// {DECLARATION}
    /// Given 支払い済みの注文
    #[test]
    fn order_can_ship() {{
    }}

    fn helper() {{
    }}
}}
'''

CSHARP = f'''
public class OrderTests {{
    /// {DECLARATION}
    /// Given 支払い済みの注文
    [Fact]
    public void OrderCanShip() {{ }}

    public void Helper() {{ }}
}}
'''

KOTLIN = f'''
class OrderTests {{
    /** {DECLARATION}
     * Given 支払い済みの注文
     */
    @Test
    fun orderCanShip() {{
    }}

    fun helper() {{
    }}
}}
'''


def _extractor() -> TreeSitterTestFunctionExtractor:
    return TreeSitterTestFunctionExtractor()


@pytest.mark.parametrize("language,source,expected_name", [
    ("go", GO, "TestOrderCanShip"),
    ("rust", RUST, "order_can_ship"),
    ("csharp", CSHARP, "OrderCanShip"),
    ("kotlin", KOTLIN, "orderCanShip"),
])
def test_only_tests_are_extracted(language, source, expected_name):
    """テストだけを取り出す。補助の関数は含めない。

    どれがテストかは言語ごとに違う。Goは名前が Test で始まること、
    Rust/C#/Kotlin は属性・注釈が付いていること。
    """
    found = _extractor().test_functions(source, language)
    assert [f["name"] for f in found] == [expected_name]


@pytest.mark.parametrize("language,source", [
    ("go", GO), ("rust", RUST), ("csharp", CSHARP), ("kotlin", KOTLIN),
])
def test_declaration_line_is_readable(language, source):
    """文書コメントから宣言行を読み取れる。飾りは adapter が落とす。"""
    found = _extractor().test_functions(source, language)
    assert DECLARATION in found[0]["doc"]

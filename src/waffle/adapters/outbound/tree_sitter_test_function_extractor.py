"""TestFunctionExtractor の tree-sitter 実装。

python / java / typescript / javascript のテストから、名前と文書コメントを
取り出す。言語ごとに違うものを、すべてここで吸収する。

| | Python | Java | TypeScript / JavaScript |
|---|---|---|---|
| テストを表すもの | 関数定義 | メソッド宣言 | 関数呼び出し |
| 名前の在り処 | 関数名 | メソッド名 | 文字列引数 |
| 文書コメントの位置 | 関数の内側 | 直前の兄弟 | 直前の兄弟 |

Pythonの文書コメントは関数の内側にあるため、どのテストのものかが構造で
決まる。他の3言語は直前の兄弟であることによって決まり、間に別のコメントや
文が挟まると対応しない（対応しない場合は宣言行を持たないテストとして扱われ、
孤立と未実装の両方で報告されるため、黙って通ることはない）。
"""
from __future__ import annotations

from tree_sitter import Language, Node, Parser
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript

from waffle.application.ports.test_function_extractor import UnsupportedLanguage

_LANGUAGE_MODULES = {
    "python": lambda: Language(tspython.language()),
    "java": lambda: Language(tsjava.language()),
    "javascript": lambda: Language(tsjavascript.language()),
    "typescript": lambda: Language(tstypescript.language_typescript()),
}

# テストとみなす呼び出しの名前（JavaScript / TypeScript）
_TEST_CALLEES = {"test", "it"}

# 落とす飾り。言語ごとに違うため、この知識はここだけが持つ
_DECORATIONS = ('"""', "'''", "/**", "*/", "/*", "//")


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _undecorate(text: str) -> str:
    """文書コメントの飾りを落とす。

    落とし方を誤ると、対応づけは正しくできているのに「宣言行が無い」と
    誤判定する。行頭のアスタリスクは、ブロックコメントの飾りとして落とす。
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        for decoration in _DECORATIONS:
            stripped = stripped.replace(decoration, "")
        stripped = stripped.strip()
        if stripped.startswith("*"):
            stripped = stripped[1:].strip()
        lines.append(stripped)
    return "\n".join(lines).strip()


def _preceding_comment(node: Node) -> str:
    """直前の兄弟がコメントならその中身を返す。

    自分に直前の兄弟が無ければ、親を辿ってから見る（呼び出しが文に包まれて
    いる言語のため）。describe等の入れ子の中でも、テストの直前にあれば取れる。
    """
    target = node
    while target.prev_sibling is None and target.parent is not None:
        target = target.parent
    previous = target.prev_sibling
    if previous is not None and "comment" in previous.type:
        return _undecorate(previous.text.decode("utf-8"))
    return ""


def _inner_docstring(function_node: Node) -> str:
    """関数本体の最初の文字列を文書コメントとして返す（Python）。"""
    body = function_node.child_by_field_name("body")
    if body is None or not body.children:
        return ""
    first = body.children[0]
    if first.type != "expression_statement" or not first.children:
        return ""
    literal = first.children[0]
    if literal.type != "string":
        return ""
    return _undecorate(literal.text.decode("utf-8"))


def _python_tests(root: Node) -> list[dict]:
    tests = []
    for node in _walk(root):
        if node.type != "function_definition":
            continue
        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        name = name_node.text.decode("utf-8")
        if not name.startswith("test_"):
            continue
        tests.append({"name": name, "doc": _inner_docstring(node)})
    return tests


def _java_tests(root: Node) -> list[dict]:
    tests = []
    for node in _walk(root):
        if node.type != "method_declaration":
            continue
        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        tests.append({"name": name_node.text.decode("utf-8"),
                      "doc": _preceding_comment(node)})
    return tests


def _js_like_tests(root: Node) -> list[dict]:
    """テスト名は識別子ではなく文字列引数で与えられる。"""
    tests = []
    for node in _walk(root):
        if node.type != "call_expression":
            continue
        callee = node.child_by_field_name("function")
        if callee is None or callee.text.decode("utf-8") not in _TEST_CALLEES:
            continue
        arguments = node.child_by_field_name("arguments")
        name = next((child.text.decode("utf-8").strip("'\"`")
                     for child in (arguments.children if arguments else [])
                     if child.type in ("string", "template_string")), "")
        tests.append({"name": name, "doc": _preceding_comment(node)})
    return tests


_COLLECTORS = {
    "python": _python_tests,
    "java": _java_tests,
    "javascript": _js_like_tests,
    "typescript": _js_like_tests,
}


class TreeSitterTestFunctionExtractor:
    """tree-sitter でテストの名前と文書コメントを取り出す。"""

    def test_functions(self, source: str, language: str) -> list[dict]:
        if language not in _LANGUAGE_MODULES:
            raise UnsupportedLanguage(language)

        parser = Parser(_LANGUAGE_MODULES[language]())
        tree = parser.parse(source.encode("utf-8"))
        if tree.root_node.has_error:
            raise SyntaxError(f"構文解析できません（{language}）")

        return _COLLECTORS[language](tree.root_node)

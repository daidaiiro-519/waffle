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
import tree_sitter_c_sharp as tscsharp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_kotlin as tskotlin
import tree_sitter_python as tspython
import tree_sitter_rust as tsrust
import tree_sitter_typescript as tstypescript

from waffle.application.ports.test_function_extractor import UnsupportedLanguage

_LANGUAGE_MODULES = {
    "python": lambda: Language(tspython.language()),
    "java": lambda: Language(tsjava.language()),
    "javascript": lambda: Language(tsjavascript.language()),
    "go": lambda: Language(tsgo.language()),
    "rust": lambda: Language(tsrust.language()),
    "csharp": lambda: Language(tscsharp.language()),
    "kotlin": lambda: Language(tskotlin.language()),
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


def _leading_comment(node: Node, skip: tuple[str, ...] = ()) -> str:
    """直前に並ぶコメントをまとめて返す。指定した種類のノードは飛ばす。

    言語によって、文書コメントと本体の間に属性が挟まる（Rustの #[test]）。
    また1行コメントが連続して1つの文書を成すこともある（Go）。直前の兄弟を
    1つだけ見る作りでは、どちらも取りこぼす。
    """
    target = node
    while target.prev_sibling is None and target.parent is not None:
        target = target.parent
    parts: list[str] = []
    previous = target.prev_sibling
    while previous is not None:
        if previous.type in skip:
            previous = previous.prev_sibling
            continue
        if "comment" not in previous.type:
            break
        parts.append(_undecorate(previous.text.decode("utf-8")))
        previous = previous.prev_sibling
    return "\n".join(reversed(parts)).strip()


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


def _go_tests(root: Node) -> list[dict]:
    """Goは名前が Test で始まる関数がテスト。文書コメントは直前の行コメント。"""
    tests = []
    for node in _walk(root):
        if node.type != "function_declaration":
            continue
        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        name = name_node.text.decode("utf-8")
        if not name.startswith("Test"):
            continue
        tests.append({"name": name, "doc": _leading_comment(node)})
    return tests


def _has_attribute(node: Node, wanted: tuple[str, ...]) -> bool:
    """直前の属性、または子に持つ注釈から、テスト指定を探す。"""
    previous = node.prev_sibling
    while previous is not None and previous.type in ("attribute_item", "comment", "line_comment"):
        if previous.type == "attribute_item":
            text = previous.text.decode("utf-8")
            if any(w in text for w in wanted):
                return True
        previous = previous.prev_sibling
    for child in _walk(node):
        if child.type in ("attribute_list", "annotation", "modifiers"):
            text = child.text.decode("utf-8")
            if any(w in text for w in wanted):
                return True
    return False


def _rust_tests(root: Node) -> list[dict]:
    """Rustは #[test] が付いた関数がテスト。属性が文書コメントと本体の間に入る。"""
    tests = []
    for node in _walk(root):
        if node.type != "function_item" or not _has_attribute(node, ("test",)):
            continue
        name_node = node.child_by_field_name("name")
        if name_node is None:
            continue
        tests.append({"name": name_node.text.decode("utf-8"),
                      "doc": _leading_comment(node, skip=("attribute_item",))})
    return tests


def _attribute_tests(node_type: str, wanted: tuple[str, ...]):
    """属性・注釈でテストを示す言語（C# / Kotlin）の収集器を作る。"""

    def collect(root: Node) -> list[dict]:
        tests = []
        for node in _walk(root):
            if node.type != node_type or not _has_attribute(node, wanted):
                continue
            name_node = node.child_by_field_name("name")
            if name_node is None:
                name_node = next((c for c in node.children if c.type == "identifier"), None)
            if name_node is None:
                continue
            tests.append({"name": name_node.text.decode("utf-8"),
                          "doc": _leading_comment(node)})
        return tests

    return collect


_COLLECTORS = {
    "python": _python_tests,
    "java": _java_tests,
    "javascript": _js_like_tests,
    "typescript": _js_like_tests,
    "go": _go_tests,
    "rust": _rust_tests,
    "csharp": _attribute_tests("method_declaration", ("Fact", "Test", "Theory")),
    "kotlin": _attribute_tests("function_declaration", ("Test",)),
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

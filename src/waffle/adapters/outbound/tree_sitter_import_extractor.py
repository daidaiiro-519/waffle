"""TreeSitterImportExtractor — ImportExtractor portのtree-sitter実装。

Python/Java/TypeScript/JavaScript/Go/Rust/C#/Kotlinの8言語に対応する。
言語ごとのノード型は推測せず、実際に解析して確かめてから書いた。同じ「依存の宣言」でも
構文木の形は言語ごとに違う。

  Python  import_from_statement / import_statement の dotted_name（相対は relative_import）
  Java    import_declaration の scoped_identifier
  TS/JS   import_statement / export_statement の source（文字列）。CommonJS の require は
          関数呼び出しなので、クエリではなく木を辿って拾う
  Go      import_spec の path（引用符つき文字列）
  Rust    use_declaration の argument（use a::{b,c} は波括弧の手前まで）
  C#      using_directive の qualified_name
  Kotlin  import の qualified_identifier
"""
from __future__ import annotations

import tree_sitter_c_sharp as tscsharp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_kotlin as tskotlin
import tree_sitter_python as tspython
import tree_sitter_rust as tsrust
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Query, QueryCursor

from waffle.application.ports.import_extractor import UnsupportedLanguage

_LANGUAGES = {
    "python": lambda: Language(tspython.language()),
    "java": lambda: Language(tsjava.language()),
    "typescript": lambda: Language(tstypescript.language_typescript()),
    "javascript": lambda: Language(tsjavascript.language()),
    "go": lambda: Language(tsgo.language()),
    "rust": lambda: Language(tsrust.language()),
    "csharp": lambda: Language(tscsharp.language()),
    "kotlin": lambda: Language(tskotlin.language()),
}

_IMPORT_QUERIES = {
    "python": """
        (import_from_statement module_name: (dotted_name) @ref)
        (import_from_statement module_name: (relative_import) @ref)
        (import_statement name: (dotted_name) @ref)
    """,
    "java": "(import_declaration (scoped_identifier) @ref)",
    "typescript": """
        (import_statement source: (string (string_fragment) @ref))
        (export_statement source: (string (string_fragment) @ref))
    """,
    "javascript": """
        (import_statement source: (string (string_fragment) @ref))
        (export_statement source: (string (string_fragment) @ref))
    """,
    "go": "(import_spec path: (interpreted_string_literal) @ref)",
    "rust": "(use_declaration argument: (_) @ref)",
    "csharp": "(using_directive (qualified_name) @ref)",
    "kotlin": "(import (qualified_identifier) @ref)",
}

# CommonJS の require はimport構文ではなく関数呼び出しなので、クエリの対象にならない。
_REQUIRE_LANGUAGES = ("javascript", "typescript")

# Python の `from パッケージ import モジュール` は、参照先がモジュール名の側にある。
# 取り込み元だけを見るとパッケージ止まりになり、ファイル単位の依存が辿れない。
_FROM_IMPORT_LANGUAGES = ("python",)


def _language(name: str) -> Language:
    if name not in _LANGUAGES:
        raise UnsupportedLanguage(name)
    return _LANGUAGES[name]()


class TreeSitterImportExtractor:
    """依存の取り出しを、言語を問わない構文解析で行う。"""
    def imports(self, source: str, language: str) -> list[str]:
        """ソースが宣言している依存を並べる。

        Args:
            source: 読む対象のソース。
            language: そのソースの言語。

        Returns:
            依存先の一覧。

        Raises:
            なし。
        """
        lang = _language(language)
        source_bytes = source.encode("utf-8")
        tree = Parser(lang).parse(source_bytes)

        found: list[tuple[int, str]] = []
        captures = QueryCursor(Query(lang, _IMPORT_QUERIES[language])).captures(tree.root_node)
        for node in captures.get("ref", []):
            found.append((node.start_byte, _clean(node.text.decode("utf-8"))))
        if language in _REQUIRE_LANGUAGES:
            found.extend(_require_references(tree.root_node))
        if language in _FROM_IMPORT_LANGUAGES:
            found.extend(_from_import_members(tree.root_node))

        # 出現順に揃える（クエリの結果は種類ごとにまとまって返るため）
        return [text for _, text in sorted(found) if text]


def _clean(text: str) -> str:
    """引用符と余分な空白を落とす。Goの参照は引用符つきの文字列として現れる。"""
    return text.strip().strip('"').strip("'").strip()


def _require_references(root) -> list[tuple[int, str]]:
    """require('...') の形の依存を、木を辿って拾う。

    クエリで書くと呼び出し先の名前が require であることを述語で絞る必要があり、
    バインディングごとに述語の扱いが違う。呼び出しの数は多くないので木を辿る。
    """
    found: list[tuple[int, str]] = []
    stack = [root]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type != "call_expression":
            continue
        callee = node.child_by_field_name("function")
        if callee is None or callee.text.decode("utf-8") != "require":
            continue
        arguments = node.child_by_field_name("arguments")
        if arguments is None:
            continue
        for argument in arguments.children:
            if argument.type != "string":
                continue
            for part in argument.children:
                if part.type == "string_fragment":
                    found.append((part.start_byte, _clean(part.text.decode("utf-8"))))
    return found


def _from_import_members(root) -> list[tuple[int, str]]:
    """`from パッケージ import モジュール` を、パッケージまで含めた参照として組み直す。

    取り込み元だけではパッケージ止まりになり、どのファイルに依存しているかが辿れない。
    取り込む名前がモジュールなのかクラスなのかは構文からは分からないので、両方を
    参照として出す。実在しない方は解決の段階で落ちる。
    """
    found: list[tuple[int, str]] = []
    stack = [root]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.type != "import_from_statement":
            continue
        module = node.child_by_field_name("module_name")
        if module is None or module.type != "dotted_name":
            continue
        prefix = module.text.decode("utf-8")
        for child in node.children:
            if child.type == "dotted_name" and child != module:
                found.append((child.start_byte, f"{prefix}.{child.text.decode('utf-8')}"))
            elif child.type == "aliased_import":
                name = child.child_by_field_name("name")
                if name is not None:
                    found.append((name.start_byte, f"{prefix}.{name.text.decode('utf-8')}"))
    return found

"""TreeSitterClassExtractor — ClassDeclarationExtractor portのtree-sitter実装。

Python/Java/TypeScript/JavaScriptの4言語（Waffleの初期対象言語群、
docs/brainstorm/brainstorm-waffle-hooks.md参照）に対応する。言語ごとの
クエリ差分（クラス名ノード型・フィールド宣言の構文）を吸収し、コア
（check_usecase_class_drift/check_aggregate_class_drift）には
「クラス名一覧」「フィールド名一覧」という言語非依存の形だけを返す。
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

# クラス定義ノードの子として現れる「名前」ノードの型は言語文法ごとに異なる
# （Python/Java/JavaScriptはidentifier、TypeScriptはtype_identifier）。
_CLASS_QUERIES = {
    "python": "(class_definition name: (identifier) @name)",
    "java": "(class_declaration name: (identifier) @name)",
    "typescript": "(class_declaration name: (type_identifier) @name)",
    "javascript": "(class_declaration name: (identifier) @name)",
    # Goは構造体を type 宣言として書く。Rustは struct_item。
    # C#/Kotlin はクラス宣言だが、名前のノード型が異なる。
    "go": "(type_declaration (type_spec name: (type_identifier) @name))",
    "rust": "(struct_item name: (type_identifier) @name)",
    "csharp": "(class_declaration name: (identifier) @name)",
    "kotlin": "(class_declaration (identifier) @name)",
}

# フィールド宣言の構文は言語ごとに全く異なる。Pythonは型注釈付きの代入文
# （dataclassの流儀）、Java/TypeScriptは明示的なフィールド宣言、JavaScriptは
# クラスフィールド宣言。
_FIELD_QUERIES = {
    "python": """
        (class_definition
          name: (identifier) @cls
          body: (block
            (expression_statement
              (assignment left: (identifier) @field type: (type))
            )
          )
        )
    """,
    "java": """
        (class_declaration
          name: (identifier) @cls
          body: (class_body
            (field_declaration
              declarator: (variable_declarator name: (identifier) @field)
            )
          )
        )
    """,
    "typescript": """
        (class_declaration
          name: (type_identifier) @cls
          body: (class_body
            (public_field_definition name: (property_identifier) @field)
          )
        )
    """,
    "javascript": """
        (class_declaration
          name: (identifier) @cls
          body: (class_body
            (field_definition property: (property_identifier) @field)
          )
        )
    """,
    "go": """
        (type_declaration
          (type_spec
            name: (type_identifier) @cls
            type: (struct_type
              (field_declaration_list
                (field_declaration name: (field_identifier) @field)
              )
            )
          )
        )
    """,
    "rust": """
        (struct_item
          name: (type_identifier) @cls
          body: (field_declaration_list
            (field_declaration name: (field_identifier) @field)
          )
        )
    """,
    "csharp": """
        (class_declaration
          name: (identifier) @cls
          body: (declaration_list
            (field_declaration
              (variable_declaration (variable_declarator (identifier) @field))
            )
          )
        )
    """,
    "kotlin": """
        (class_declaration
          (identifier) @cls
          (class_body
            (property_declaration (variable_declaration (identifier) @field))
          )
        )
    """,
}

_LANGUAGE_MODULES = {
    "python": lambda: Language(tspython.language()),
    "java": lambda: Language(tsjava.language()),
    "typescript": lambda: Language(tstypescript.language_typescript()),
    "javascript": lambda: Language(tsjavascript.language()),
    "go": lambda: Language(tsgo.language()),
    "rust": lambda: Language(tsrust.language()),
    "csharp": lambda: Language(tscsharp.language()),
    "kotlin": lambda: Language(tskotlin.language()),
}


def _language(language: str) -> Language:
    factory = _LANGUAGE_MODULES.get(language)
    if factory is None:
        raise ValueError(f"サポート対象外の言語です: {language}（対応: {sorted(_LANGUAGE_MODULES)}）")
    return factory()


class TreeSitterClassExtractor:
    def class_names(self, source: str, language: str) -> list[str]:
        lang = _language(language)
        tree = Parser(lang).parse(source.encode("utf-8"))
        query = Query(lang, _CLASS_QUERIES[language])
        captures = QueryCursor(query).captures(tree.root_node)
        source_bytes = source.encode("utf-8")
        return [source_bytes[n.start_byte:n.end_byte].decode("utf-8") for n in captures.get("name", [])]

    def field_names(self, source: str, language: str, class_name: str) -> list[str]:
        lang = _language(language)
        tree = Parser(lang).parse(source.encode("utf-8"))
        query = Query(lang, _FIELD_QUERIES[language])
        source_bytes = source.encode("utf-8")
        fields: list[str] = []
        for _, captures in QueryCursor(query).matches(tree.root_node):
            cls_node = captures["cls"][0]
            if source_bytes[cls_node.start_byte:cls_node.end_byte].decode("utf-8") != class_name:
                continue
            fields.append(source_bytes[captures["field"][0].start_byte:captures["field"][0].end_byte].decode("utf-8"))
        return fields

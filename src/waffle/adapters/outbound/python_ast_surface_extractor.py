"""python_ast_surface_extractor — Pythonの受け口から入口を取り出すadapter。

構文木で読む。正規表現で関数の宣言を拾うと、文字列やコメントの中の似た並びを
入口と誤認する。

参照している名前は、呼び出しの対象として現れた識別子だけを集める。どれが操作の
名前かはここでは決めない——決めると、この層が業務の語彙を知ることになる。
"""
from __future__ import annotations

import ast

from waffle.application.ports.surface_extractor import UnsupportedLanguage

_SUPPORTED = ("python",)


class PythonAstSurfaceExtractor:
    """Pythonのソースから入口を取り出す。"""

    def surfaces(self, source: str, language: str) -> list[dict]:
        """ソースに含まれる入口を列挙する。

        Args:
            source: 受け口のソースコード。
            language: そのソースの言語。

        Returns:
            入口ごとに {name, params, references} を持つ辞書の並び。

        Raises:
            UnsupportedLanguage: python以外を渡された。
        """
        if language not in _SUPPORTED:
            raise UnsupportedLanguage(language)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        found: list[dict] = []
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            found.append({
                "name": node.name,
                "params": [a.arg for a in node.args.args if a.arg not in ("self", "cls")],
                "references": sorted(_called_names(node)),
            })
        return found


def _called_names(node: ast.AST) -> set[str]:
    """その入口が呼び出している名前を集める。

    Args:
        node: 走査の起点となる構文木のノード。

    Returns:
        呼び出しの対象として現れた識別子の集合。

    Raises:
        なし。
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        target = child.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names

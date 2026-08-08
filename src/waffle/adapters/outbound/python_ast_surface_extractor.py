"""python_ast_surface_extractor — Pythonの受け口から入口を取り出すadapter。

構文木で読む。正規表現で関数の宣言を拾うと、文字列やコメントの中の似た並びを
入口と誤認する。

参照している名前は、呼び出しの対象として現れた識別子だけを集める。どれが操作の
名前かはここでは決めない——決めると、この層が業務の語彙を知ることになる。
"""
from __future__ import annotations

import ast
import re

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
            入口ごとに {name, params, paramDescriptions, references} を持つ辞書の並び。

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
                "paramDescriptions": _param_descriptions(node),
                "references": sorted(_invoked_names(node) or _called_names(node)),
            })
        return found


def _param_descriptions(node: ast.AST) -> dict[str, str]:
    """その入口が、引数ごとに利用者へ見せている説明を集める。

    置き場所は口によって違う。命令行は選択肢の宣言に、道具呼び出しは文書コメントの
    引数の節に持つ。どちらも利用者の目に触れるので、どちらも見る。

    Args:
        node: 入口の関数のノード。

    Returns:
        引数の名前から、利用者へ見せている説明への対応。無い引数は含まない。

    Raises:
        なし。
    """
    found: dict[str, str] = {}

    defaults = [None] * (len(node.args.args) - len(node.args.defaults))
    defaults += list(node.args.defaults)
    for argument, default in zip(node.args.args, defaults):
        if not isinstance(default, ast.Call):
            continue
        for keyword in default.keywords:
            if keyword.arg == "help" and isinstance(keyword.value, ast.Constant):
                found[argument.arg] = keyword.value.value

    doc = ast.get_docstring(node) or ""
    if "Args:" in doc:
        section = doc.split("Args:", 1)[1]
        for stop in ("Returns:", "Raises:"):
            section = section.split(stop, 1)[0]
        for line in section.splitlines():
            matched = re.match(r"\s{4}(\w+):\s*(.+?)\s*$", line)
            if matched:
                found.setdefault(matched.group(1), matched.group(2))
    return found


def _invoked_names(node: ast.AST) -> set[str]:
    """その入口が、作ってすぐ呼び出している名前を集める。

    1つの入口が複数の操作を組み立てることがある（片方を相手の部品として渡す等）。
    作っただけの名前まで数えると、部品として渡された側もその入口の操作だと
    見なしてしまう。呼び出されたものだけが、その入口が差し出している操作。

    Args:
        node: 走査の起点となる構文木のノード。

    Returns:
        作られた直後にメソッドを呼ばれた識別子の集合。

    Raises:
        なし。
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Attribute):
            continue
        target = child.value
        if isinstance(target, ast.Call) and isinstance(target.func, ast.Name):
            names.add(target.func.id)
    return names


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

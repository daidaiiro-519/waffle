"""canonical_naming — 宣言された表記に従って識別子とファイル名を導く純粋なドメインサービス。

どの表記を採るかはここでは決めない。coding-standard の naming ブロックが宣言し、
この関数はその宣言どおりに変換するだけを担う。表記をここが決めていた頃は
「ファイル名は言語を問わず snake_case」という規則をコードが持っており、
ファイル名と公開型名の一致が言語仕様で要求される Java や、モジュール名が
ファイル名になる Rust では成立しなかった。

drift-check 系の複数 usecase が、宣言と実装の対応を機械的に検証するために使う。
"""
from __future__ import annotations

import re

_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
_SEPARATOR = re.compile(r"(?<!^)[-_]")


def _split_words(name: str, separator: str) -> str:
    """語の区切りを、指定された記号へ揃える。

    区切りは2種類ある。大文字の始まりと、既に置かれている区切り記号。
    後者を見ないと、区切り記号で綴られた識別子（仕様の識別子はこの形）を
    1語とみなし、どの表記を指定しても変換されないまま返る。

    先頭の区切りは残す。非公開を先頭の記号で表す規約があるため、
    正規化して組み立て直すとその規約と衝突する。
    """
    return _SEPARATOR.sub(separator, _BOUNDARY.sub(separator, name)).lower()


def to_snake_case(name: str) -> str:
    """識別子を snake_case へ変換する。

    Args:
        name: 変換する識別子。

    Returns:
        snake_case の識別子。
    """
    return _split_words(name, "_")


def _to_kebab_case(name: str) -> str:
    return _split_words(name, "-")


def _to_camel_case(name: str) -> str:
    head, *rest = to_snake_case(name).split("_")
    return head + "".join(part.title() for part in rest)


def _to_pascal_case(name: str) -> str:
    return "".join(part.title() for part in to_snake_case(name).split("_"))


_CASES = {
    "snake": to_snake_case,
    "kebab": _to_kebab_case,
    "camel": _to_camel_case,
    "pascal": _to_pascal_case,
    "upper-snake": lambda name: to_snake_case(name).upper(),
}

_TRANSFORMS = {
    "": lambda name: name,
    "identity": lambda name: name,
    "pascal-to-snake": to_snake_case,
    "pascal-to-kebab": _to_kebab_case,
    "lower": str.lower,
}


def apply_case(name: str, case: str) -> str:
    """宣言された表記へ識別子を変換する。

    Args:
        name: 変換する識別子。
        case: coding-standard の naming.cases が宣言した表記。

    Returns:
        変換後の識別子。

    Raises:
        ValueError: 宣言に無い表記を指定された場合。既定へ黙って倒すと、
            綴り間違いが「合っている」ことになるため拒否する。
    """
    if case not in _CASES:
        raise ValueError(f"宣言に無い表記です: {case}（対応: {sorted(_CASES)}）")
    return _CASES[case](name)


def case_for(naming: dict, artifact: str, visibility: str = "") -> str:
    """成果物の種別に対して宣言された表記を返す。

    Args:
        naming: coding-standard の naming ブロック。
        artifact: 種別（module / type / function / constant / field）。
        visibility: 可視性で表記が変わる言語での絞り込み。空なら問わない。

    Returns:
        宣言された表記。

    Raises:
        ValueError: その種別の表記が宣言されていない場合。既定へ黙って倒すと、
            宣言の無いスタックで誤った名前を正しいものとして扱ってしまう。
    """
    for entry in naming.get("cases", []):
        if entry.get("artifact") != artifact:
            continue
        if visibility and entry.get("visibility", "") != visibility:
            continue
        return entry["case"]
    raise ValueError(f"{artifact} の表記が naming.cases に宣言されていません")


def file_name(type_name: str, naming: dict) -> str:
    """宣言された規則に従って、型名から実装ファイル名を導く。

    Args:
        type_name: 由来となる型・操作の名前。
        naming: coding-standard の naming ブロック。fileNameTransform と
            fileNameSuffix を読む。

    Returns:
        拡張子まで含むファイル名。

    Raises:
        ValueError: 宣言に無い変換を指定された場合。
    """
    transform = naming.get("fileNameTransform", "identity")
    if transform not in _TRANSFORMS:
        raise ValueError(f"宣言に無い変換です: {transform}（対応: {sorted(_TRANSFORMS)}）")
    return _TRANSFORMS[transform](type_name) + naming.get("fileNameSuffix", "")

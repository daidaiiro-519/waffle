"""lifecycle_guard — schema の x-lifecycle 宣言を読んで status 遷移の可否を判定する。

JSON Schema は構造/値の検証はできるが状態遷移は表現できないため、
遷移表そのものは schema に宣言的データ（x-lifecycle）として持ち、
この関数はそれを読むだけの薄い executor（imperative な集約クラスは持たない）。
"""
from __future__ import annotations


def next_status(schema: dict, current_status: str | None, command: str) -> str | None:
    """schema の x-lifecycle に従い、command 実行後の status を返す。遷移が定義されていなければ None。

    Args:
        schema: 遷移を宣言しているschema。
        current_status: いまのstatus。
        command: 実行しようとしている操作。

    Returns:
        遷移後のstatus。その遷移が宣言されていなければ None。

    Raises:
        なし。
    """
    lifecycle = schema.get("x-lifecycle")
    if lifecycle is None:
        return None
    for transition in lifecycle["transitions"]:
        if transition["command"] == command and transition["from"] == current_status:
            return transition["to"]
    return None

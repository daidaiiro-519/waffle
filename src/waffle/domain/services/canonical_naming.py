"""canonical_naming — usecase specのoperationName(PascalCase)から、対応する実装
ファイルのモジュール名(snake_case)を導出する純粋なドメインサービス。
check_usecase_class_drift.pyが、宣言された操作名と実装クラス名の対応関係を
機械的に検証するために使う（coding-standardの命名規約のコード側実装）。
"""
from __future__ import annotations

import re

_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def operation_name_to_module_name(operation_name: str) -> str:
    """'CheckScenarioDrift' -> 'check_scenario_drift' のようにPascalCaseを
    snake_caseへ変換する。"""
    return _BOUNDARY.sub("_", operation_name).lower()

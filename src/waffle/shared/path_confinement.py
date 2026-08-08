"""path_confinement — パストラバーサル検知の純粋なユーティリティ。業務ロジックを
含まない汎用の技術的関心事なので、shared（domain/servicesではない）に置く。
agg-document(Document集約)の不変条件「Document のパス解決は、いかなる operation・
command からも常にプロジェクトルート内に閉じ込められる」を実装するために使われる。
ポート・実I/Oを一切必要としない（パス文字列だけを扱う）。
"""
from __future__ import annotations

from pathlib import Path

def is_confined(path: str) -> bool:
    """path がプロジェクトルート内に閉じ込められているか（パストラバーサルを含まないか）を判定する。

    Args:
        path: 判定する対象のパス。

    Returns:
        プロジェクトルート内に閉じていれば True。

    Raises:
        なし。
    """
    return ".." not in Path(path).parts

def is_within_project_root(directory: str) -> bool:
    """directory がプロジェクトルート自身またはその配下にあるかを判定する（ディレクトリ横断

    Args:
        directory: 判定する対象のディレクトリ。

    Returns:
        プロジェクトルート自身またはその配下にあれば True。

    Raises:
        なし。
    """
    root = Path.cwd().resolve()
    target = Path(directory).resolve()
    return target == root or root in target.parents

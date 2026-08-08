"""schema_versioning — schemaRef(例: 'Foo/v2')からバージョン番号を取り出す純粋な
ドメインサービス。check_schema_version_drift.pyがドキュメントの参照バージョンと
最新バージョンを数値として正しく比較するために使う（文字列ソートでは 'v10' が
'v2' より前に来てしまう誤りを避ける）。
"""
from __future__ import annotations

def version_number(ref: str) -> int | None:
    """'Foo/v2' や 'v2' からバージョン番号を取り出す。解釈できなければNone。

    Args:
        ref: 版を取り出す対象の文字列。

    Returns:
        版の番号。解釈できなければ None。

    Raises:
        なし。
    """
    version = ref.rpartition("/")[2]
    if not version.startswith("v") or not version[1:].isdigit():
        return None
    return int(version[1:])


def latest_version(versions: list[str]) -> str | None:
    """並んだ版のうち最も新しいものを返す。

    番号として読める版だけを対象にする。文字列の大小で比べると v10 が v9 より
    前に来るので、必ず番号で比べる。

    Args:
        versions: その schema が持つ版の一覧（例: ["v1", "v2", "v10"]）。

    Returns:
        最も新しい版。番号として読める版が1つも無ければ None。

    Raises:
        なし。
    """
    numbered = [v for v in versions if version_number(v) is not None]
    if not numbered:
        return None
    return max(numbered, key=version_number)


def has_version(ref: str) -> bool:
    """schemaRef が版まで指しているか。'Foo/v2' は真、'Foo' は偽。

    Args:
        ref: 判定する schemaRef。

    Returns:
        版を含んでいれば True。

    Raises:
        なし。
    """
    return "/" in ref and version_number(ref) is not None

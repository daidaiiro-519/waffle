"""source_root_resolution — architecture文書から概念の実装配置を解決する application層の共通ヘルパー。

CLIとMCPの両方がこの解決を必要とし、以前は同じ判定が両方の合成ルートに重複して
置かれていた。合成ルートは配線専用に保つ規約（コンポジションルート自体に業務
ロジックを書かない）に反しており、かつ inbound adapter が domain service を
直接呼ぶ形になっていた。判断をここへ引き上げ、アダプターはResultを各プロトコルの
形へ translate するだけにする。

配置の導出そのもの（sourceRootとplacementの結合）は業務判断を含まない計算なので
domain/services/concept_source_root.py が担う。ここはport経由の読込と、
どのエラーコードで失敗を表すかの編成だけを担当する。
"""
from __future__ import annotations

from dataclasses import dataclass

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.concept_source_root import (
    declares_per_file,
    package_name_from_reference,
    resolve_source_root,
)
from waffle.shared.result import Err, Ok, Result

__all__ = ["SearchUnit", "resolve_src_root", "resolve_search_unit",
           "resolve_directory_scoped_root"]

_ARCHITECTURE_PATH = ".waffle/documents/coding/{architecture_ref}.json"


@dataclass(frozen=True)
class SearchUnit:
    """その概念を、1つのファイルで探すか、配置ディレクトリで探すか。

    宣言を読めたかどうかを一緒に運ぶ。読めた結果のファイル単位と、読めなかった
    ためのファイル単位は、同じ探し方でも意味が違う。前者は宣言に従った状態で、
    後者はそのプロジェクトがまだ決めていない状態。呼び出し側がこれを見分けられ
    ないと、宣言の欠落を報告できない。
    """

    per_file: bool
    root: str | None = None
    declared: bool = True


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


def resolve_src_root(
    documents: DocumentRepository,
    src_root: str | None,
    architecture_ref: str | None,
    concept: str,
) -> Result[str]:
    """実装ファイルの配置ルートを解決する。

    src_root が明示されていればそれを優先し、無ければ architecture_ref が指す
    architecture文書の layout.sourceRoot と conceptPlacement から導出する。

    Args:
        documents: architecture文書を読むためのDocumentRepository。
        src_root: 明示指定された配置ルート。指定されていれば他を見ない。
        architecture_ref: 参照するarchitecture documentのdocumentId。
        concept: 解決したい概念（usecase / aggregate 等）。

    Returns:
        解決した配置ルートを持つ Ok、または失敗を表す Err。
        失敗のコードは MISSING_PARAM / ARCHITECTURE_REF_NOT_FOUND /
        ARCHITECTURE_REF_UNRESOLVED のいずれか。
    """
    if src_root:
        return Ok(src_root)
    if not architecture_ref:
        return _err("MISSING_PARAM", "srcRoot または architectureRef のいずれかが必要です")
    try:
        document = documents.load(_ARCHITECTURE_PATH.format(architecture_ref=architecture_ref))
    except FileNotFoundError:
        return _err(
            "ARCHITECTURE_REF_NOT_FOUND",
            f"architecture document が見つかりません: {architecture_ref}",
        )
    content = document.get("content", {})
    resolved = resolve_source_root(
        content.get("layout", {}),
        content.get("conceptPlacement", {}).get("items", []),
        concept,
        package=package_name_from_reference(architecture_ref, "architecture") or "",
    )
    if not resolved:
        return _err(
            "ARCHITECTURE_REF_UNRESOLVED",
            f"{architecture_ref} の layout.sourceRoot / conceptPlacement"
            f"（concept={concept}）から解決できません",
        )
    return Ok(resolved)


def resolve_search_unit(
    documents: DocumentRepository,
    architecture_ref: str | None,
    concept: str,
) -> SearchUnit:
    """その概念をどの単位で探すかを、architecture の宣言から決める。

    layout.granularity がその概念に「1ファイルに1つ」を宣言していればファイル
    単位、宣言していなければ conceptPlacement が与える配置ディレクトリ単位。
    どちらで探すかを決める権限は architecture にあり、検査はそれを読むだけにする。

    宣言そのものへ辿り着けないとき（参照が渡されない・その文書が無い・配置を
    導けない）はファイル単位に落とすが、declared を False にしてそのことを伝える。
    黙って落とすと、宣言に従った結果と区別がつかなくなる。

    Args:
        documents: architecture文書を読むためのDocumentRepository。
        architecture_ref: 参照するarchitecture documentのdocumentId。
        concept: 探索の単位を知りたい概念（aggregate / usecase / value-object 等）。

    Returns:
        探し方を表す SearchUnit。ディレクトリ単位のときだけ root を持つ。

    Raises:
        なし。宣言へ辿り着けないことは失敗ではなく、declared=False で表す。
    """
    if not architecture_ref:
        return SearchUnit(per_file=True, declared=False)
    try:
        document = documents.load(
            _ARCHITECTURE_PATH.format(architecture_ref=architecture_ref))
    except FileNotFoundError:
        return SearchUnit(per_file=True, declared=False)
    content = document.get("content", {})
    if declares_per_file(content.get("layout", {}), concept):
        return SearchUnit(per_file=True)
    resolved = resolve_src_root(documents, None, architecture_ref, concept)
    if not isinstance(resolved, Ok):
        return SearchUnit(per_file=True, declared=False)
    return SearchUnit(per_file=False, root=resolved.value)


def resolve_directory_scoped_root(
    documents: DocumentRepository,
    architecture_ref: str | None,
    concept: str,
) -> str | None:
    """その概念を配置ディレクトリ単位で探すべきときにだけ、その配置を返す。

    ファイル単位で探す概念については None を返す。探し方そのものを知りたい場合は
    resolve_search_unit を使う——こちらは配置だけを取り出す薄い形。

    Args:
        documents: architecture文書を読むためのDocumentRepository。
        architecture_ref: 参照するarchitecture documentのdocumentId。
        concept: 解決したい概念。

    Returns:
        ディレクトリ単位で探すならその配置、そうでなければ None。

    Raises:
        なし。
    """
    return resolve_search_unit(documents, architecture_ref, concept).root

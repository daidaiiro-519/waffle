"""class_index — 配置ディレクトリの直下から、クラス名とその定義元の対応を作る application層の共通ヘルパー。

集約ルート・操作・値オブジェクトのいずれも、ディレクトリ単位で探すときに
同じ問い（この名前のクラスはこの配置のどこにあるか）を立てる。同じ走査を
検査ごとに書き写すと、片方だけが下位のディレクトリへ降りるといった食い違いが
静かに生まれる。

下位のディレクトリへは降りない。conceptPlacement が指すのは1つのディレクトリで
あり、降りると宣言されていない区画まで拾うため。
"""
from __future__ import annotations

from waffle.application.ports.class_declaration_extractor import ClassDeclarationExtractor
from waffle.application.ports.document_repository import DocumentRepository


def build_class_index(
    documents: DocumentRepository,
    extractor: ClassDeclarationExtractor,
    root: str,
    file_name_suffix: str,
    language: str,
) -> dict[str, list[tuple[str, str]]]:
    """配置ディレクトリの直下を走査し、クラス名から定義元への対応を作る。

    同じ名前が複数のファイルにあるときは、どちらとも決めずに両方を覚えておく。
    先に当たった方を黙って採ると、答えがファイル名の順で決まってしまう。

    Args:
        documents: ソースを読むためのDocumentRepository。
        extractor: ソースからクラス名を取り出すport。
        root: 走査する配置ディレクトリ。
        file_name_suffix: 対象とする拡張子（naming の宣言から渡す）。
        language: ソースの言語。

    Returns:
        クラス名から (ファイルパス, ソース) の一覧への対応。配置ディレクトリが
        存在しなければ空の対応。

    Raises:
        なし。配置がまだ無いことは失敗ではなくドリフトなので、空を返す。
    """
    index: dict[str, list[tuple[str, str]]] = {}
    try:
        paths = documents.list_files(root, f"*{file_name_suffix}")
    except FileNotFoundError:
        return index
    for path in sorted(paths):
        try:
            source = documents.read_text(path)
        except FileNotFoundError:  # pragma: no cover — 列挙直後に消えた場合
            continue
        for name in extractor.class_names(source, language):
            index.setdefault(name, []).append((path, source))
    return index

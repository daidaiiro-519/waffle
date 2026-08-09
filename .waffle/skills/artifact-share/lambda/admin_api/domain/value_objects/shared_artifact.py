"""共有アーティファクトが持つ値。

どれも書き換えられない。集約が状態を変えるときは、変えた結果を持つ新しい値を
受け取る形にして、不変条件を守る道をメソッドに限る。

対象の仕様: agg-shared-artifact
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.value_objects.identifier import ARTIFACT_ID_LENGTH, ensure

# 公開されているかどうか
PUBLISHED = "PUBLISHED"
SUSPENDED = "SUSPENDED"

# 目印の出どころ
EXTRACTED = "extracted"   # 中身から取り出した
MANUAL = "manual"         # 人が与えた


@dataclass(frozen=True)
class ArtifactId:
    """公開された共有アーティファクトを一意に指す短いID。

    通る形は字種と桁数で決まる。作られ方によらずここで確かめるのは、作る手立てを
    外の口へ出したあとも、その経路を通らない値が入り込まないようにするため。
    """

    value: str

    def __post_init__(self) -> None:
        ensure(self.value, ARTIFACT_ID_LENGTH, "共有アーティファクトの識別子")


@dataclass(frozen=True)
class PublisherId:
    """公開した人を指す識別子。招かれた者にのみ与えられる。"""

    value: str


@dataclass(frozen=True)
class ArtifactStatus:
    """公開されているかどうか。PUBLISHED と SUSPENDED のいずれか。"""

    value: str

    def is_published(self) -> bool:
        """いま公開されているか。

        Returns:
            公開されていれば True。

        Raises:
            なし。
        """
        return self.value == PUBLISHED

    def is_suspended(self) -> bool:
        """いま公開を止めているか。

        Returns:
            止めていれば True。

        Raises:
            なし。
        """
        return self.value == SUSPENDED


@dataclass(frozen=True)
class ArtifactDescriptor:
    """共有アーティファクトに添えられた識別子・種別・題名・要約・分類の目印。

    中身に書かれていれば取り出し、書かれていなければ題名だけを人が与える。
    種別と分類の目印は保持するだけで、値の意味を解釈しない——解釈すると、
    中身に書ける値が誰に見せるかを左右してしまう。

    5つの値には一組全体に不変条件がかかるので、組み立てる道をここに閉じる。
    どこから取り出したかという読み取りの手順は、業務サービスの側が担う。
    """

    document_id: str = ""
    doc_type: str = ""
    title: str = ""
    description: str = ""
    labels: tuple[str, ...] = ()
    source: str = MANUAL

    @staticmethod
    def of(read: "ReadFromContent", fallback_title: str = "") -> "ArtifactDescriptor":
        """読み取れたものと、人が与えた題名から、一組を組み立てる。

        契約の目印が揃っていれば中身から取り出したものとして扱い、揃って
        いなければ題名だけを人が与えたものとして扱う。この採否がこの値の
        不変条件そのものなので、外で決めさせない。

        Args:
            read: 中身から読み取れたもの。
            fallback_title: 目印が揃っていないときに人が与える題名。

        Returns:
            組み立てた一組。

        Raises:
            なし。
        """
        if read.detected:
            return ArtifactDescriptor(
                document_id=read.document_id, doc_type=read.doc_type,
                title=read.title, description=read.description,
                labels=read.labels, source=EXTRACTED)
        return ArtifactDescriptor(title=fallback_title or read.title, source=MANUAL)


@dataclass(frozen=True)
class ReadFromContent:
    """中身から読み取れたもの。採否はまだ決まっていない。

    読み取りの手順（どのタグをどう見るか）は業務サービスが担い、ここはその
    結果を運ぶだけ。素の辞書で運ぶと、欄の増減が誰にも見えなくなる。
    """

    document_id: str = ""
    doc_type: str = ""
    title: str = ""
    description: str = ""
    labels: tuple[str, ...] = ()
    external_refs: int = 0
    detected: bool = False

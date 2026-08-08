"""check domain service drift — bounded-context specが宣言する業務サービスの
group（実装ファイル単位）が、実際に対応するファイルとして実在するかを検証する
application use case。

usecase/aggregateと異なり、業務サービスは「1サービス＝1ファイル」という規約を
持たない（凝集した能力ごとに複数サービスが同じファイルに同居してよい）ため、
クラス名・フィールドの機械的突き合わせではなく、groupから導出したファイルの
存在確認のみを行う。内容の正しさ（振る舞いが壊れていないか）はTDDが別途担保する。
"""
from __future__ import annotations

from waffle.application.ports.document_repository import DocumentRepository
from waffle.domain.services.canonical_naming import file_name
from waffle.shared.path_confinement import is_confined
from waffle.shared.result import Err, Ok, Result


def _err(code: str, message: str) -> Err:
    return Err(message, [code])


class CheckDomainServiceDrift:
    """業務サービスの宣言と、その実装の食い違いを見つける。"""
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    def run(self, documents_root: str, src_root: str, naming: dict) -> Result[dict]:
        """業務サービスの宣言と、その実装の食い違いを見つける。

        Args:
            documents_root: 突き合わせの対象とする仕様の置き場所。
            src_root: 実装を探す配置ルート。
            naming: 名前の綴りの流儀を宣言している規約の naming ブロック。

        Returns:
            その操作の結果を持つ Ok、または失敗を表す Err。

        Raises:
            なし。失敗は結果型で返す。
        """
        if not is_confined(documents_root) or not is_confined(src_root):
            return _err("INVALID_PATH", "パストラバーサルは許可されません")
        try:
            doc_paths = self._documents.list_files(documents_root, "**/*.json")
        except FileNotFoundError:
            return _err("INVALID_PATH", f"ディレクトリが見つかりません: {documents_root}")
        # 宣言された配置がまだ存在しないことは、引数の誤りではなくドリフトそのもの。
        # 規約を先に書いて実装を後から合わせる進め方では、この状態が正常に起こる。
        # ここで止めると「まだ何も出来ていない」ことを報告できない

        missing_implementation_file: list[dict] = []
        checked_groups: set[str] = set()

        for doc_path in doc_paths:
            doc = self._documents.load(doc_path)
            if doc.get("specKind") != "bounded-context":
                continue
            for service in doc.get("content", {}).get("domainServices", {}).get("items", []):
                group = service.get("group")
                if not group or group in checked_groups:
                    continue
                checked_groups.add(group)
                expected_path = f"{src_root}/{file_name(group, naming)}"
                try:
                    self._documents.read_text(expected_path)
                except FileNotFoundError:
                    missing_implementation_file.append({
                        "documentId": doc["documentId"], "group": group, "expectedPath": expected_path,
                    })

        return Ok({"missing_implementation_file": missing_implementation_file})

"""ファイルシステム adapter（DocumentRepository 実装）。

document.json の読み書きおよび任意テキスト/ディレクトリ走査をローカル
ファイルシステム上で行う。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from waffle.application.ports.document_repository import DocumentRepository

class FsDocumentRepository(DocumentRepository):
    """documentの読み書きを、ファイルシステムの上で行う。"""
    def load(self, path: str) -> dict:
        """1つのdocumentを読む。

        Args:
            path: 読む対象の置き場所。

        Returns:
            読み込んだdocument。

        Raises:
            FileNotFoundError: その道にファイルが無い。
        """
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def save(self, path: str, document: dict) -> None:
        """1つのdocumentを残す。整形の仕方は集約の取り決めに従う。

        Args:
            path: 書き出す先。
            document: 書き出す中身。

        Returns:
            なし。

        Raises:
            なし。
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def write_text(self, path: str, text: str) -> None:
        """文字列をそのまま書き出す。

        Args:
            path: 書き出す先。
            text: 書き出す中身。

        Returns:
            なし。

        Raises:
            なし。
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def resolve_real_path(self, path: str) -> str:
        """symlinkを辿って、実体の道を求める。

        Args:
            path: 辿る対象の道。

        Returns:
            実体の道。

        Raises:
            なし。
        """
        p = Path(path)
        return str(p.resolve()) if p.exists() else ""

    def link(self, canonical: str, path: str) -> None:
        """正本への参照を、指定された場所に張る。

        Args:
            canonical: 参照先となる正本の道。
            path: 参照を張る場所。

        Returns:
            なし。

        Raises:
            なし。
        """
        target = Path(path)
        canonical_abs = Path(canonical).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        # targetの親ディレクトリ自体がcanonical側へのシンボリックリンクの場合、targetは
        # 実体としてcanonicalと同一ファイルを指す。この状態でunlinkするとcanonical自体を
        # 消してしまい、続く symlink_to が自己参照リンクを作ってしまう（実際に発生した事故）。
        # 親解決後の絶対パスが一致する場合は何もしない（既に同一ファイルなので不要）。
        if target.exists() and target.resolve() == canonical_abs:
            return
        if target.is_symlink() or target.exists():
            target.unlink()
        rel = os.path.relpath(canonical_abs, target.parent.resolve())
        target.symlink_to(rel)

    def read_text(self, path: str) -> str:
        """ファイルの中身を文字列として読む。

        Args:
            path: 読む対象の置き場所。

        Returns:
            読み込んだ文字列。

        Raises:
            FileNotFoundError: その道にファイルが無い。
        """
        return Path(path).read_text(encoding="utf-8")

    def list_json(self, directory: str) -> list[str]:
        """そのディレクトリにあるdocumentを並べる。

        Args:
            directory: 並べる対象のディレクトリ。

        Returns:
            documentの道の一覧。

        Raises:
            FileNotFoundError: そのディレクトリが無い。
        """
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(str(p) for p in d.glob("*.json"))

    def list_dirs(self, directory: str) -> list[str]:
        """そのディレクトリの直下にあるディレクトリを並べる。

        Args:
            directory: 並べる対象のディレクトリ。

        Returns:
            ディレクトリの道の一覧。

        Raises:
            FileNotFoundError: そのディレクトリが無い。
        """
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(p.name for p in d.iterdir() if p.is_dir())

    def list_files(self, directory: str, pattern: str) -> list[str]:
        """形に当てはまるファイルを並べる。降りるかどうかは形が決める。

        Args:
            directory: 並べる対象のディレクトリ。
            pattern: 当てはめる形。配下まで届かせるなら二重の星印を含める。

        Returns:
            当てはまったファイルの道の一覧。

        Raises:
            FileNotFoundError: そのディレクトリが無い。
        """
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(str(p) for p in d.glob(pattern))

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
    def load(self, path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def save(self, path: str, document: dict) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def write_text(self, path: str, text: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def link(self, canonical: str, path: str) -> None:
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
        return Path(path).read_text(encoding="utf-8")

    def list_json(self, directory: str) -> list[str]:
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(str(p) for p in d.glob("*.json"))

    def list_dirs(self, directory: str) -> list[str]:
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(p.name for p in d.iterdir() if p.is_dir())

    def list_files(self, directory: str, pattern: str) -> list[str]:
        d = Path(directory)
        if not d.is_dir():
            raise FileNotFoundError(directory)
        return sorted(str(p) for p in d.glob(pattern))

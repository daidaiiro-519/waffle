"""DocumentRepository port — document.json の読み書きの Secondary Port。"""
from __future__ import annotations

from typing import Protocol


class DocumentRepository(Protocol):
    def load(self, path: str) -> dict:
        """path の document.json を dict で返す。"""
        ...

    def save(self, path: str, document: dict) -> None:
        """document を path に書き込む。"""
        ...

    def write_text(self, path: str, text: str) -> None:
        """レンダリング成果物などのテキストを path に書き込む。"""
        ...

    def link(self, canonical: str, path: str) -> None:
        """canonical への相対シンボリックリンクを path に作る（既存ファイル/リンクは置き換える）。"""
        ...

    def read_text(self, path: str) -> str:
        """path のファイルを生テキストで返す（scan / raw フォールバック用）。無ければ FileNotFoundError。"""
        ...

    def resolve_real_path(self, path: str) -> str:
        """path のシンボリックリンクを辿った実体パスを返す。path に何も無ければ空文字を返す
        （まだ何も置かれていない配置先は、誰にも所有されていないことを意味する）。"""
        ...

    def list_json(self, directory: str) -> list[str]:
        """directory 直下の *.json パス一覧（昇順）。ディレクトリが無ければ FileNotFoundError。"""
        ...

    def list_dirs(self, directory: str) -> list[str]:
        """directory 直下のサブディレクトリ名一覧（昇順）。ディレクトリが無ければ FileNotFoundError。"""
        ...

    def list_files(self, directory: str, pattern: str) -> list[str]:
        """directory 直下の pattern(glob) に一致するファイルパス一覧（昇順）。ディレクトリが無ければ FileNotFoundError。"""
        ...

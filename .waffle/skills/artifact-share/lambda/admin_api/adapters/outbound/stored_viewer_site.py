"""閲覧の面への配置を、保管と配信ドメインで実現する。

置き場所（p/{識別子}/ と proj/{識別子}/）、画面の雛形とその差し込み、URLの
組み立てをここだけが知る。application はこれらを一切知らない。

雛形を差し込む先の目印（{{アーティファクトID}} 等）は日本語のままにしてある。
雛形を書く人が読んで分かる名前であることを優先しており、機械が解釈する識別子
ではない。
"""
from __future__ import annotations

import hashlib
import json

ARTIFACT_ID_MARK = "{{アーティファクトID}}"
DISPLAY_NAME_MARK = "{{表示名}}"
PROJECT_ID_MARK = "{{プロジェクトID}}"

HTML = "text/html; charset=utf-8"
JSON = "application/json"


class StoredViewerSite:
    def __init__(self, store, wrapper_template: str = "", project_page: str = "",
                 viewer_domain: str = ""):
        self._store = store
        self._wrapper = wrapper_template
        self._project_page = project_page
        self._domain = viewer_domain

    def place_artifact(self, artifact_id: str, content: str, display_name: str) -> None:
        # アップロードされたものは書き換えずにそのまま置く
        self._store.put(_content_key(artifact_id), content, HTML)

        # 閲覧画面はこちらが組み立てる。中身には触れない
        page = self._wrapper.replace(ARTIFACT_ID_MARK, artifact_id)
        page = page.replace(DISPLAY_NAME_MARK, display_name)
        self._store.put(_index_key(artifact_id), page, HTML)

        # 使った雛形の版を、この面の側で控える。雛形を直したときに置き直しが
        # 要るものを見分けるためのもので、共有アーティファクトの状態ではない
        self._store.put(_version_key(artifact_id),
                        hashlib.sha256(self._wrapper.encode("utf-8")).hexdigest(),
                        "text/plain; charset=utf-8")

    def replace_artifact_content(self, artifact_id: str, content: str) -> None:
        self._store.put(_content_key(artifact_id), content, HTML)

    def read_artifact_content(self, artifact_id: str) -> str:
        try:
            return self._store.get(_content_key(artifact_id))
        except Exception:
            return ""

    def place_project(self, project_id: str) -> None:
        page = (self._project_page or "").replace(PROJECT_ID_MARK, project_id)
        self._store.put(f"proj/{project_id}/index.html", page, HTML)

    def place_project_listing(self, project_id: str, display_name: str,
                              artifacts: list[dict]) -> None:
        self._store.put(
            f"proj/{project_id}/index.json",
            json.dumps({"name": display_name, "artifacts": artifacts}, ensure_ascii=False),
            JSON,
        )

    def artifact_url(self, artifact_id: str) -> str:
        return f"https://{self._domain or '{viewer-domain}'}/p/{artifact_id}/"

    def project_url(self, project_id: str) -> str:
        return f"https://{self._domain or '{viewer-domain}'}/proj/{project_id}/"


def _content_key(artifact_id: str) -> str:
    return f"p/{artifact_id}/content.html"


def _index_key(artifact_id: str) -> str:
    return f"p/{artifact_id}/index.html"


def _version_key(artifact_id: str) -> str:
    return f"p/{artifact_id}/page-version.txt"

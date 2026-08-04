"""公開。

アップロードされたHTMLを受け取り、閲覧できる状態にして、URLとトークンを返す。
利用者の確認・中身の検査・artifactIdとトークンの発行・配置を担う。公開の経路は
これひとつだけで、中身の検査を経ずに保管へ書き込む手段は用意しない。

外部への接続は依存として受け取る。実際の接続を組み立てるのは main.py だけで、
ここは渡されたものだけを使う。検証のときは偽の依存を渡せる。

対象の仕様: uc-publish-artifact / agg-shared-artifact
"""

from __future__ import annotations

import hashlib
import html.parser
import json
import re
import secrets

from ports import Deps
import time
from dataclasses import dataclass
from typing import Callable

# 読み間違えやすい文字（l, o, 0, 1）を外した英数字
ID_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
ID_LENGTH = 8
TOKEN_GROUPS = 3
TOKEN_GROUP_LENGTH = 4

# 受け取るHTMLの上限。これを超えるものは、署名付きの経路で直接受け渡す設計へ移す
MAX_CONTENT_BYTES = 5 * 1024 * 1024

# トークンの既定の有効期限（秒）。0 は無期限
DEFAULT_TOKEN_TTL = 0


class PublishError(Exception):
    """公開できない理由を、仕様のエラーコードとともに伝える。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ── 中身の検査 ──────────────────────────────────────────

class _HeadParser(html.parser.HTMLParser):
    """head の meta と title、そして外部への参照を拾う。

    中身を書き換えるためではなく、読み取るためだけに解析する。
    解析に失敗しても公開は止めない（検査は補助であって、公開を拒む判定ではない）。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title = ""
        self.external = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta" and "name" in a:
            self.meta[a["name"].lower()] = a.get("content", "").strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and _is_external(a.get("src", "")):
            self.external += 1
        elif tag == "img" and _is_external(a.get("src", "")):
            self.external += 1
        elif tag == "link" and "stylesheet" in a.get("rel", "").lower():
            if _is_external(a.get("href", "")):
                self.external += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()


def _is_external(url: str) -> bool:
    """別のホストを指しているか。data: での埋め込みは外部ではない。"""
    return bool(re.match(r"^(https?:)?//", url.strip(), re.IGNORECASE))


def inspect_html(content: str) -> dict:
    """HTMLから、控えるべき情報と外部への参照の件数を読み取る。

    契約のmetaタグ（id と type）が揃っていれば、利用者に何も尋ねずに公開できる。
    揃っていなければ、題名だけを尋ねる。
    """
    parser = _HeadParser()
    try:
        parser.feed(content)
    except Exception:
        pass  # 解析に失敗しても、控える情報が減るだけで公開は妨げない

    meta = parser.meta
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return {
        "documentId": meta.get("id", ""),
        "docType": meta.get("type", ""),
        "title": meta.get("title", "") or parser.title,
        "description": meta.get("description", ""),
        "tags": tags,
        "externalRefs": parser.external,
        "detected": bool(meta.get("id") and meta.get("type")),
    }


# ── 発行 ────────────────────────────────────────────────

def new_artifact_id() -> str:
    return "".join(secrets.choice(ID_ALPHABET) for _ in range(ID_LENGTH))


def new_token() -> str:
    groups = [
        "".join(secrets.choice(ID_ALPHABET) for _ in range(TOKEN_GROUP_LENGTH))
        for _ in range(TOKEN_GROUPS)
    ]
    return "-".join(groups)


def token_record(token: str, now: int, ttl: int = DEFAULT_TOKEN_TTL, generation: int = 1) -> str:
    """トークンの保管に残す記録。

    トークンそのものは残さず、照合できる形だけを残す。有効期限と世代番号を
    添えるのは、再発行しただけでは閲覧者の手元の記録が生き残るため。
    照合の側は、値と世代の両方が一致したときだけ通す。
    """
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]
    expires = now + ttl if ttl > 0 else 0
    return f"{digest}|{expires}|{generation}"


# ── 公開 ────────────────────────────────────────────────

def publish(request: dict, deps: Deps) -> dict:
    """アップロードされたHTMLを公開し、URLとトークンを返す。

    途中で失敗したときに開ける状態のものを残さないことを、書き込む順序で保証する。
    トークンを最後に書くため、それ以前で失敗すると、置かれたファイルは残るものの
    トークンが存在せず、閲覧ゲートがすべての要求を拒む（誰も開けない）。

    置いたものを消して回る作りにはしない。この管理APIには削除の権限を与えておらず、
    与えると、破られたときの被害が反応や記録にまで及ぶため。到達できないまま
    残ったファイルの片付けは、権限を持つ責任者の運用として行う。
    """
    publisher = deps.identify(request.get("authorization", ""))
    if not publisher:
        raise PublishError("NOT_INVITED", "公開できるのは招かれた利用者だけです。")

    content = request.get("html", "")
    if not content or not content.strip():
        raise PublishError("EMPTY_CONTENT", "中身が空です。")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        raise PublishError("CONTENT_TOO_LARGE", "受け取れる大きさを超えています。")

    found = inspect_html(content)
    display_name = (request.get("displayName") or "").strip()

    if found["detected"]:
        title = found["title"] or display_name
        meta_source = "extracted"
    else:
        title = display_name or found["title"]
        meta_source = "manual"
        if not display_name:
            # 題名だけを尋ねる。ここで尋ねる項目を増やさない
            raise PublishError("NAME_REQUIRED", "表示名を入力してください。")

    artifact_id = new_artifact_id()
    token = new_token()
    now = deps.now()

    index_key = f"p/{artifact_id}/index.html"
    content_key = f"p/{artifact_id}/content.html"
    meta_key = f"meta/{artifact_id}.json"

    try:
        # アップロードされたものは書き換えずにそのまま置く
        deps.store.put(content_key, content, "text/html; charset=utf-8")

        # 閲覧画面はこちらが組み立てる。中身には触れない
        viewer = deps.wrapper_template.replace("{{アーティファクトID}}", artifact_id)
        viewer = viewer.replace("{{表示名}}", title)
        deps.store.put(index_key, viewer, "text/html; charset=utf-8")

        record = {
            "artifactId": artifact_id,
            "name": title,
            "status": "active",
            "projects": [],
            "metaSource": meta_source,
            "docType": found["docType"],
            "documentId": found["documentId"],
            "description": found["description"],
            "tags": found["tags"],
            "uploadedBy": publisher,
            "externalRefs": found["externalRefs"],
            "contentHash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "wrapperHash": hashlib.sha256(deps.wrapper_template.encode("utf-8")).hexdigest(),
            "publishedAt": now,
            "updatedAt": now,
        }
        deps.store.put(meta_key, json.dumps(record, ensure_ascii=False), "application/json")

        # トークンは最後に書く。ここまで成功して初めて開ける状態になる
        deps.keys.put(f"token:{artifact_id}", token_record(token, now))
    except PublishError:
        raise
    except Exception as e:
        # トークンを書く前に失敗しているため、置かれたものは誰にも開けない
        raise PublishError("PUBLISH_FAILED", f"公開できませんでした: {e}") from e

    domain = deps.viewer_domain or "{viewer-domain}"
    return {
        "artifactId": artifact_id,
        "token": token,               # 返すのはこの一度きり。保管には残さない
        "url": f"https://{domain}/p/{artifact_id}/",
        "descriptor": {
            "documentId": found["documentId"],
            "docType": found["docType"],
            "title": title,
            "description": found["description"],
            "tags": found["tags"],
        },
        "metaSource": meta_source,
        "externalRefs": found["externalRefs"],
        "needsName": False,
        "tokenShownOnce": True,       # 呼び出し側へ、二度は示せないことを伝える
    }

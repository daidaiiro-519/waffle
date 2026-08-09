"""上げられたHTMLから、控えるべき情報と外部への参照を読み取る。

読み取るためだけに解析する。中身は書き換えない——公開したものが手元のものと
一字一句同じであることが、この仕組みの前提であるため。

解析に失敗しても公開は止めない。検査は補助であって、公開を拒む判定ではない。

ここが担うのは読み取りだけで、読み取れた値と人が与えた値のどちらを採るかは
決めない。その採否は一組全体にかかる不変条件なので、目印そのものが持つ。
変わる理由が別なので分けてある——書かれ方が変われば読み取りが変わり、業務の
決めごとが変われば採否が変わる。

対象の仕様: uc-publish-artifact / agg-shared-artifact
"""
from __future__ import annotations

import html.parser
import re

from domain.value_objects.shared_artifact import ReadFromContent


def is_external(url: str) -> bool:
    """別のホストを指しているか。data: での埋め込みは外部ではない。

    Args:
        url: 判定する参照先。

    Returns:
        別のホストを指していれば True。data: での埋め込みは外部ではない。

    Raises:
        なし。
    """
    return bool(re.match(r"^(https?:)?//", url.strip(), re.IGNORECASE))


class _HeadParser(html.parser.HTMLParser):
    """head の meta と title、そして外部への参照を拾う。"""

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
        elif tag == "script" and is_external(a.get("src", "")):
            self.external += 1
        elif tag == "img" and is_external(a.get("src", "")):
            self.external += 1
        elif tag == "link" and "stylesheet" in a.get("rel", "").lower():
            if is_external(a.get("href", "")):
                self.external += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()


def inspect_html(content: str) -> ReadFromContent:
    """HTMLから、控えるべき情報と外部への参照の件数を読み取る。

    契約の目印（id と type）が揃っていれば、利用者に何も尋ねずに公開できる。
    揃っているかどうかは伝えるだけで、揃っていないときに何を尋ねるかは
    ここでは決めない。

    Args:
        content: 読み取る対象のHTML。

    Returns:
        読み取れたもの。採否はまだ決まっていない。

    Raises:
        なし。
    """
    parser = _HeadParser()
    try:
        parser.feed(content)
    except Exception:
        pass  # 解析に失敗しても、控える情報が減るだけで公開は妨げない

    meta = parser.meta
    labels = tuple(t.strip() for t in meta.get("tags", "").split(",") if t.strip())
    return ReadFromContent(
        document_id=meta.get("id", ""),
        doc_type=meta.get("type", ""),
        title=meta.get("title", "") or parser.title,
        description=meta.get("description", ""),
        labels=labels,
        external_refs=parser.external,
        detected=bool(meta.get("id") and meta.get("type")),
    )

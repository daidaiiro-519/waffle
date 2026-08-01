"""寄せられたコメントを投稿者へ届ける。

閲覧者は閲覧トークンで開いた画面から読み書きし、投稿者は本人確認を通った
画面から読む。指しているものは同じコメントだが、通ってよい条件が違うため、
経路を分けたままにする。

閲覧トークンは一度しか示されず投稿者の手元に残らないので、閲覧の経路は
使い回せない。自分のものを読むために自分で発行したトークンを控えておく
必要がある作りにはしない。

ここは読むだけを担う。コメントへ書き込む手段は持たない。持つと、寄せられた
指摘を投稿者が書き換えられることになる。

対象の仕様: uc-read-comments / uc-export-artifact
引き継ぎ: handoff-read-export
"""

from __future__ import annotations

import json

from manage import Caller, Deps, _read_meta


def _prefix(artifact_id: str) -> str:
    return f"comments/{artifact_id}/"


def _record_id(key: str) -> str:
    """鍵から、そのコメント1件を指す識別子を取り出す。返信先はこれで指される。"""
    return key.rsplit("/", 1)[-1].removesuffix(".json")


def read(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """寄せられたコメントを、古いものから順に返す。

    差し替えの区切りも同じ並びに含める。分けて返すと、どの指摘が差し替え
    前のものかを画面側が組み立て直すことになる。

    読めない記録は飛ばして残りを返し、飛ばした件数を添える。1件の不具合で
    その共有アーティファクトの反応がすべて見えなくなるのを避ける。黙って
    落とさないのは、投稿者が「これで全部だ」と思い込むため。

    保存されている形のまま返す。表示用に整えるのは画面側が行う。
    """
    # 扱える範囲の判定は既にあるものを通す。拒み方（見つからないものとして
    # 扱う）も自動的に揃う
    _read_meta(deps, caller, artifact_id)

    rows, unreadable = [], 0
    # 鍵は先頭に時刻を持つため、鍵の順がそのまま寄せられた順になる
    for key in sorted(deps.store.list(_prefix(artifact_id))):
        try:
            record = json.loads(deps.store.get(key))
        except Exception:
            unreadable += 1
            continue
        record["id"] = _record_id(key)
        record.setdefault("kind", "comment")
        rows.append(record)

    return {"artifactId": artifact_id, "comments": rows, "unreadable": unreadable}


def export(deps: Deps, caller: Caller, artifact_id: str) -> dict:
    """中身と、それまでに寄せられたコメントをまとめて返す。

    読むだけの操作で、公開状態も閲覧トークンもコメントも変えない。公開を
    止める操作と切り離してあるのは、止めるかどうかを決める前に中身を
    確かめたい場面があるため。

    1つのファイルにまとめるのは画面側が行う。ここで保管へ書くと、取り出しが
    読むだけの操作でなくなる。

    閲覧トークンは含めない。取り出したものが渡り歩いても、それだけで開ける
    状態にならないようにする。
    """
    meta = _read_meta(deps, caller, artifact_id)

    try:
        content = deps.store.get(f"p/{artifact_id}/content.html")
    except Exception:
        content = ""

    found = read(deps, caller, artifact_id)

    return {
        "artifactId": artifact_id,
        "name": meta.get("name", ""),
        "docType": meta.get("docType", ""),
        "documentId": meta.get("documentId", ""),
        "description": meta.get("description", ""),
        "tags": meta.get("tags", []),
        "status": meta.get("status", ""),
        "publishedAt": meta.get("publishedAt", 0),
        "updatedAt": meta.get("updatedAt", 0),
        "content": content,
        "comments": found["comments"],
        "unreadable": found["unreadable"],
    }

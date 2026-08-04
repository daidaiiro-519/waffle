#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3"]
# ///
"""adopt_existing_view_tokens.py — 移行前から渡してある閲覧トークンを、記録へ迎え入れる。

1つの対象へ複数の閲覧トークンを渡せるようにする前は、渡してある1本の照合の形が
閲覧の面（KVS）にしか無く、公開する側の記録（S3）は持っていなかった。

そのままにすると、次に閲覧トークンを1本発行した時点で、閲覧の面へ渡す顔ぶれが
「記録にある分」だけに置き換わる。記録に無い既存の1本は顔ぶれから外れ、
渡した相手は理由も分からず開けなくなる。投稿者の側には成功が返るので、
気づく手がかりが無い。

そこで、いま閲覧の面が持っている記録を読み、対応する記録が無ければ1本として
迎え入れる。名前は「移行前から渡していたもの」とし、あとから一覧で見分けて
外せるようにする。

1回だけ実行する。2度目以降は迎え入れるものが無く、何も書かない。

使い方:
  adopt_existing_view_tokens.py           何をするかだけを表示する
  adopt_existing_view_tokens.py --apply   実際に書き込む
"""
from __future__ import annotations

import json
import os
import sys
import time

ADOPTED_NAME = "移行前から渡していたもの"
CLOSED = "DISABLED"


def main() -> int:
    import boto3

    apply = "--apply" in sys.argv
    bucket = os.environ["CONTENT_BUCKET"]
    kvs_arn = os.environ["KVS_ARN"]
    s3 = boto3.client("s3")
    kvs = boto3.client("cloudfront-keyvaluestore")

    adopted, skipped = [], []
    for prefix, id_field, key_prefix in (("meta/", "artifactId", "token:"),
                                         ("projects/", "projectId", "proj:")):
        for key in _keys(s3, bucket, prefix):
            try:
                record = json.loads(_read(s3, bucket, key))
            except Exception as e:
                print(f"  読めない: {key} ({e})")
                continue
            if record.get("viewTokens"):
                skipped.append(key)
                continue

            target = record.get(id_field, "")
            grant = _current_grant(kvs, kvs_arn, f"{key_prefix}{target}")
            if grant is None:
                skipped.append(key)
                continue

            fingerprint, expires = grant
            record["viewTokens"] = [{
                "tokenId": _token_id(target),
                "name": ADOPTED_NAME,
                "fingerprint": fingerprint,
                "expiresAt": expires,
                "status": "ACTIVE",
                "issuedAt": record.get("publishedAt") or record.get("createdAt")
                or int(time.time()),
            }]
            adopted.append(key)
            if apply:
                s3.put_object(Bucket=bucket, Key=key,
                              Body=json.dumps(record, ensure_ascii=False).encode("utf-8"),
                              ContentType="application/json", ChecksumAlgorithm="CRC32")

    print(f"\n迎え入れる: {len(adopted)}件   そのまま: {len(skipped)}件")
    for key in adopted:
        print(f"  {'書き込んだ' if apply else '書き込む予定'}: {key}")
    if adopted and not apply:
        print("\n実際に書き込むには --apply を付けて実行してください。")
    return 0


def _keys(s3, bucket: str, prefix: str) -> list[str]:
    keys, token = [], None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        res = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in res.get("Contents", [])]
        if not res.get("IsTruncated"):
            return keys
        token = res["NextContinuationToken"]


def _read(s3, bucket: str, key: str) -> str:
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")


def _current_grant(kvs, arn: str, key: str) -> tuple[str, int] | None:
    """閲覧の面がいま持っている1本を読む。無い・止めている・読めないなら None。"""
    try:
        raw = kvs.get_key(KvsARN=arn, Key=key)["Value"]
    except Exception:
        return None
    if not raw or raw == CLOSED:
        return None
    # 移行前の形は {照合の形}|{期限}|{世代}。世代は使わない
    parts = raw.split(";")[0].split("|")
    if not parts[0]:
        return None
    try:
        expires = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        expires = 0
    return parts[0], expires


def _token_id(target: str) -> str:
    """迎え入れた1本を指す識別子。対象ごとに決まるので、2度実行しても同じ値になる。"""
    return f"adopted-{target}"[:24]


if __name__ == "__main__":
    raise SystemExit(main())

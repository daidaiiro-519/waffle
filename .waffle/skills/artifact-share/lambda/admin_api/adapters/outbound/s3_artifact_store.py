"""共有アーティファクトの保管を、S3 で実現する。

application は「置く・取り出す・並べる」としか言わない。どの入れ物へ
どう置くかはここだけが知る。
"""
from __future__ import annotations

from adapters.outbound.object_store import ObjectStore


class S3ArtifactStore(ObjectStore):
    def __init__(self, bucket: str):
        import boto3

        self._bucket = bucket
        self._s3 = boto3.client("s3")

    def put(self, key, body, content_type):
        # 使う照合方式をこちらで決める。実行環境の既定に任せると、
        # 追加の部品を要求されて書き込めないことがある
        self._s3.put_object(Bucket=self._bucket, Key=key,
                      Body=body.encode("utf-8"), ContentType=content_type,
                      ChecksumAlgorithm="CRC32")

    def get(self, key):
        return self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read().decode("utf-8")

    def list(self, prefix):
        keys, token = [], None
        while True:
            kw = {"Bucket": self._bucket, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            res = self._s3.list_objects_v2(**kw)
            keys += [o["Key"] for o in res.get("Contents", [])]
            if not res.get("IsTruncated"):
                return keys
            token = res["NextContinuationToken"]

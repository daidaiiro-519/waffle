"""閲覧トークンの保管を、配信の面が同期で読める鍵と値の保管で実現する。

ここに置いた値は、閲覧の面（別のランタイム）が同じ形で読む。形の宣言は
infra/contract/ にあり、両方がそこを読む。
"""
from __future__ import annotations

from adapters.outbound.key_value_store import KeyValueStore


class KvsViewTokenStore(KeyValueStore):
    """閲覧トークンの記録を、配信の面が同期で読める鍵と値の保管の上で扱う。"""
    def __init__(self, kvs_arn: str):
        import boto3

        self._arn = kvs_arn
        self._kvs = boto3.client("cloudfront-keyvaluestore")

    def put(self, key, value):
        """1つの鍵に値を書く。

        Args:
            key: 書き込む先の鍵。
            value: 書き込む値。

        Returns:
            なし。

        Raises:
            なし。
        """
        etag = self._kvs.describe_key_value_store(KvsARN=self._arn)["ETag"]
        self._kvs.put_key(KvsARN=self._arn, Key=key, Value=value, IfMatch=etag)

    def get(self, key):
        """1つの鍵の値を読む。

        Args:
            key: 読む対象の鍵。

        Returns:
            その鍵の値。無ければ空。

        Raises:
            なし。
        """
        return self._kvs.get_key(KvsARN=self._arn, Key=key)["Value"]

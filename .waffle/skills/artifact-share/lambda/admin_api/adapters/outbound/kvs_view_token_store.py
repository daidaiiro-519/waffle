"""閲覧トークンの保管を、配信の面が同期で読める鍵と値の保管で実現する。

ここに置いた値は、閲覧の面（別のランタイム）が同じ形で読む。形の宣言は
infra/contract/ にあり、両方がそこを読む。
"""
from __future__ import annotations


class KvsViewTokenStore:
    def __init__(self, kvs_arn: str):
        import boto3

        self._arn = kvs_arn
        self._kvs = boto3.client("cloudfront-keyvaluestore")

    def put(self, key, value):
        etag = self._kvs.describe_key_value_store(KvsARN=self._arn)["ETag"]
        self._kvs.put_key(KvsARN=self._arn, Key=key, Value=value, IfMatch=etag)

    def get(self, key):
        return self._kvs.get_key(KvsARN=self._arn, Key=key)["Value"]

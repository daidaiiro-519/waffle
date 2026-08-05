"""保管と鍵置き場の偽物。すべてのテストがここの1組を使う。

同じ口の偽物を複数のファイルに分けて定義すると、少しずつ食い違い、実物なら
失敗する場面で偽物が成功してテストが緑になる。実際にこの2つは、公開の
テストと管理のテストで別々に育ち、片方だけが読み出しを持ち、片方だけが
失敗を作れる状態になっていた。
"""


class FakeStore:
    """保管への読み書きを覚えているだけの偽物。失敗させることもできる。"""

    def __init__(self, objects=None, fail_on=None):
        self.objects = dict(objects or {})
        self.fail_on = fail_on

    def put(self, key, body, content_type):
        if self.fail_on and self.fail_on in key:
            raise RuntimeError("書き込みに失敗しました")
        self.objects[key] = {"body": body, "content_type": content_type}

    def get(self, key):
        if key not in self.objects:
            raise KeyError(key)
        return self.objects[key]["body"]

    def list(self, prefix):
        return [k for k in sorted(self.objects) if k.startswith(prefix)]


class FakeKeyStore:
    """閲覧の面へ渡す鍵の置き場の偽物。書き込みを失敗させることもできる。"""

    def __init__(self, keys=None, fail=False):
        self.keys = dict(keys or {})
        self.fail = fail

    def put(self, key, value):
        if self.fail:
            raise RuntimeError("トークンの保管に失敗しました")
        self.keys[key] = value

    def get(self, key):
        if key not in self.keys:
            raise KeyError(key)
        return self.keys[key]

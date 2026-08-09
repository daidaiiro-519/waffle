from domain.value_objects.identifier import ID_ALPHABET
from domain.value_objects.project import ProjectId
from domain.value_objects.shared_artifact import ArtifactId
from domain.value_objects.view_token import ViewTokenId

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
    """閲覧の面へ渡す鍵の置き場の偽物。書き込みを失敗させることもできる。

    この口に読み取りは無い。業務のLambdaは書くだけで、読むのは別のランタイム
    （閲覧ゲート）だからである。検証が書いたものを見たいときは written を直接見る
    ——口の読み取りとして確かめると、本番に無い経路を固定することになる。
    """

    def __init__(self, written=None, fail=False):
        self.written = dict(written or {})
        self.fail = fail

    def put(self, key, value):
        if self.fail:
            raise RuntimeError("トークンの保管に失敗しました")
        self.written[key] = value


class FakeIdGenerator:
    """決まった値を順に返す発行の口。

    乱数を使うと、同じ検証が回ごとに別の値で走る。テスト規約が「時刻・乱数・
    ID生成は決定的な値に固定する」と定めているため、ここで固定する。

    使う字は業務の語彙が定める字種から取る。読み違えやすい文字を避ける決まりは
    偽の口にもかかっており、外れた値を作ると識別子として通らない。
    """

    def __init__(self):
        self._n = 0

    def _mark(self) -> str:
        """1回ごとに違う、字種に収まる1文字。"""
        self._n += 1
        return ID_ALPHABET[self._n % len(ID_ALPHABET)]

    def new_artifact_id(self):
        return ArtifactId("aaaaaaa" + self._mark())

    def new_project_id(self):
        return ProjectId("ppppp" + self._mark())

    def new_view_token_id(self):
        return ViewTokenId("ttttt" + self._mark())

    def new_view_token_secret(self) -> str:
        return "aaaa-bbbb-ccc" + self._mark()

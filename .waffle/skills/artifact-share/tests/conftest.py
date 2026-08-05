"""テストが実装を見つけられるようにする。

テストはコードの根の外（スキル直下）にある。層を持たないと宣言した領域で
あり、根の内側に置くと「どの層にも属さないファイル」として毎回報告される
ためで、Waffle自身のテストと同じ置き方になる。

その代わり、実装への道はここで1度だけ通す。各テストが自分で数えると
（parents[1] か parents[2] か）、階層を1つ変えるたびに全ファイルが壊れる。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parent / "lambda" / "admin_api"

for path in (CODE, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

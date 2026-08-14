"""テストが実装と出荷物を見つけられるようにする。

テストはコードの根の外（スキル直下）にある。層を持たないと宣言した領域で
あり、根の内側に置くと「どの層にも属さないファイル」として毎回報告される
ためで、Waffle自身のテストと同じ置き方になる。

その代わり、道はここで1度だけ通す。各テストが自分で数えると（parents[1] か
parents[2] か）、階層を1つ変えるたびに全ファイルが壊れる。

通す道は2つ。実装への道（取り込みのため）と、スキル直下への道（出荷物や
ランタイムをまたぐ取り決めを読むため）。後者は SKILL として配る——出荷物を
確かめるテストは階層の深さがまちまちで、自分で数えると同じことが起きる。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# スキル直下。出荷物（閲覧画面・閲覧ゲート・管理画面）と、ランタイムをまたぐ
# 取り決め（infra/contract/）と、手元で動くプログラム（scripts/）がここにある
SKILL = HERE.parent

CODE = SKILL / "lambda" / "admin_api"

for path in (CODE, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

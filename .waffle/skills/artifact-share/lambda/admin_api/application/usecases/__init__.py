"""業務の操作を1つずつ置く。

1ファイルに1つのユースケースを置き、ファイル名は spec が宣言する操作名から
導かれる。check-usecase-class-drift が宣言とここを機械的に突き合わせるので、
宣言に無い操作をここへ置くことも、宣言したのに置き忘れることもできない。

architecture: architecture-artifact-share の conceptPlacement（usecase）
"""

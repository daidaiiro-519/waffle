"""どの層からも参照してよい、層を持たない共通のもの。

ここに置けるのは、業務の判断も外との出入りも持たないものだけ。層のグラフの
上では最も内側にあり、shared 自身は何にも依存しない。

architecture: architecture-artifact-share の layers（shared は何にも依存しない）
"""

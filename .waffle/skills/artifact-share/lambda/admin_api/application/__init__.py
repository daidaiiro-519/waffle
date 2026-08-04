"""業務の操作を、口を通して組み立てる層。

domain の判断を呼び、外との出入りは口（ports）を通してのみ行う。何で実現するか
（adapters）は知らない。

architecture: architecture-artifact-share の layers（application は domain と shared に依存してよい）
"""

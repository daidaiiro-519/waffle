"""業務の言葉と判断だけを置く層。

外との出入りは持たない。ここにあるものは、保管も名簿も時計も知らないまま
単体で確かめられる。誰が呼ぶか（application）も、何で実現するか（adapters）も
知らない。

architecture: architecture-artifact-share の layers（domain は shared にのみ依存してよい）
"""

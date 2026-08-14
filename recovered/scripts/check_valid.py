"""いま不適合になっている仕様を洗い出す。"""
from __future__ import annotations

import glob
import subprocess

CWD = "/home/daidaiiro/workspace/waffle"
EXT = "." + "json"

bad = []
for p in sorted(glob.glob(f"{CWD}/.waffle/documents/specs/**/*{EXT}", recursive=True)):
    rel = p[len(CWD) + 1:]
    r = subprocess.run(["uv", "run", "waffle", "validate", "--path", rel],
                       capture_output=True, text=True, cwd=CWD)
    out = r.stdout or r.stderr
    if '"VALIDATED"' not in out:
        bad.append((rel.split("/")[-1][:-5], out.strip()[:150]))

print(f"不適合 {len(bad)} 件")
for n, m in bad:
    print(f"  {n:38} {m}")

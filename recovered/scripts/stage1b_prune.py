"""重複を消したことで使われなくなった取り込みを落とす。

読み手を惑わせる残骸は、移す前に落とす。移動はこれを別の場所へ運ぶだけになる。
"""
from __future__ import annotations

import ast
import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")


def unused(path: pathlib.Path) -> set[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            imported |= {a.asname or a.name for a in n.names}
        elif isinstance(n, ast.Import):
            imported |= {(a.asname or a.name).split(".")[0] for a in n.names}
    used = {x.id for x in ast.walk(tree) if isinstance(x, ast.Name)}
    used |= {x.value.id for x in ast.walk(tree)
             if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)}
    return {i for i in imported if i not in used}


def prune(rel: str) -> None:
    p = TESTS / rel
    names = unused(p)
    if not names:
        print("そのまま:", rel)
        return
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    out, dropped, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        # 括弧で折り返した取り込みは、まとめて1つの文として扱う
        if re.match(r"^from .* import \($", line.rstrip()):
            block = [line]
            while not block[-1].rstrip().endswith(")"):
                i += 1
                block.append(lines[i])
            body = "".join(block)
            kept = [n for n in re.findall(r"^\s{4}(\w+),?", body, re.M) if n not in names]
            removed = [n for n in re.findall(r"^\s{4}(\w+),?", body, re.M) if n in names]
            if removed:
                dropped += removed
                if kept:
                    head = block[0]
                    out.append(head.replace(" (", " ") .rstrip("(\n") + ", ".join(kept) + "\n")
                # 全部消えたら行ごと落とす
            else:
                out += block
            i += 1
            continue
        m = re.match(r"^from [\w.]+ import (.+?)(\s+#.*)?$", line.rstrip())
        if m:
            items = [x.strip() for x in m.group(1).split(",")]
            kept = [x for x in items if x.split(" as ")[-1].strip() not in names]
            if len(kept) != len(items):
                dropped += [x for x in items if x not in kept]
                if kept:
                    out.append(re.sub(r"import .+?(\s+#.*)?$",
                                      "import " + ", ".join(kept) + (m.group(2) or ""),
                                      line.rstrip()) + "\n")
                i += 1
                continue
        m = re.match(r"^import (\w+)$", line.rstrip())
        if m and m.group(1) in names:
            dropped.append(m.group(1))
            i += 1
            continue
        out.append(line)
        i += 1
    p.write_text("".join(out), encoding="utf-8")
    print(f"落とした: {rel} → {', '.join(sorted(dropped))}")


for rel in ("test_comments.py", "test_transfer.py", "test_publish.py", "test_manage.py"):
    prune(rel)

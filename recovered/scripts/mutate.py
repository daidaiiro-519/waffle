"""検出力を、変異を注入して機械的に裏取りする。

対象は2箇所だけに絞る——証明の検証と、保管と集約の翻訳。どちらも壊れても
他のどの検証も落ちない領域なので、検出力が本物かを確かめる価値が高い。
全体へ一律に掛けるのは費用が見合わない。

生き残った変異（落ちなかったもの）は、その振る舞いを誰も守っていないことを指す。
"""
from __future__ import annotations

import pathlib
import subprocess

SKILL = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share")
LAMBDA = SKILL / "lambda" / "admin_api" / "adapters" / "outbound"

# （対象ファイル, 元の綴り, 変異後, 何を壊したか）
MUTANTS = [
    # ── 証明の検証 ──────────────────────────────────
    ("cognito.py", 'if header.get("alg") != "RS256"', 'if False',
     "署名の方式を確かめない"),
    ("cognito.py", 'if claims.get("iss") != issuer', 'if False',
     "発行元を確かめない"),
    ("cognito.py", 'if claims.get("aud") != client_id', 'if False',
     "宛先のアプリを確かめない"),
    ("cognito.py", 'if claims.get("token_use") != "id"', 'if False',
     "証明の種類を確かめない"),
    ("cognito.py", 'if claims.get("exp", 0) <= now', 'if False',
     "期限を確かめない"),
    # ── 保管と集約の翻訳 ────────────────────────────
    ("stored_shared_artifact_repository.py", 'record.get("uploadedBy", "")', '""',
     "公開した人を読まない"),
    ("stored_shared_artifact_repository.py", 'record.get("contentHash", "")', '""',
     "中身の指紋を読まない"),
    ("stored_shared_artifact_repository.py",
     'SUSPENDED if record.get("status") == STORED_SUSPENDED else PUBLISHED',
     'PUBLISHED', "公開状態をいつも公開中と読む"),
    ("stored_shared_artifact_repository.py", '"contentHash": artifact.content_fingerprint.value,',
     '"contentHash": "",', "中身の指紋を書き戻さない"),
    ("stored_shared_artifact_repository.py", 'record = dict(base or {})', 'record = {}',
     "集約が知らない欄を引き継がない"),
    ("stored_project_repository.py", 'record.get("scope"', '(lambda *_: "PERSONAL")(',
     "出し入れの範囲をいつも個人と読む"),
]


def run() -> tuple[int, str]:
    r = subprocess.run(["uv", "run", "pytest", "tests/", "-q", "-x", "--no-header"],
                       capture_output=True, text=True, cwd=SKILL)
    return r.returncode, r.stdout


killed, survived = 0, []
for name, old, new, what in MUTANTS:
    p = LAMBDA / name
    original = p.read_text(encoding="utf-8")
    if old not in original:
        print(f"  ？ 綴りが見つからない（{name}）: {old[:50]}")
        continue
    p.write_text(original.replace(old, new, 1), encoding="utf-8")
    code, _ = run()
    p.write_text(original, encoding="utf-8")
    if code == 0:
        survived.append((name, what))
        print(f"  生き残り: {what}（{name}）")
    else:
        killed += 1
        print(f"  仕留めた: {what}")

print(f"\n仕留めた {killed} / 生き残り {len(survived)}")
for name, what in survived:
    print(f"  誰も守っていない: {what}（{name}）")

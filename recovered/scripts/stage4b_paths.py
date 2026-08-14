"""スキル根への道を、自分で数えるのをやめて1か所から受け取る形へ揃える。"""
from __future__ import annotations

import pathlib
import re

TESTS = pathlib.Path(
    "/home/daidaiiro/workspace/waffle/.waffle/skills/artifact-share/tests")

# 自分で数えている箇所を、conftest が配る道へ置き換える
REPLACEMENTS = [
    ("adapters/inbound/contract/test_document_meta_contract.py",
     '    (Path(__file__).resolve().parents[1] / "infra" / "contract" / "document-meta.json")',
     '    (SKILL / "infra" / "contract" / "document-meta.json")'),
    ("adapters/inbound/contract/test_token_record_contract.py",
     '    (Path(__file__).resolve().parents[1] / "infra" / "contract" / "token-records.json")',
     '    (SKILL / "infra" / "contract" / "token-records.json")'),
    ("cli/unit/test_smoke.py",
     "ROOT = Path(__file__).resolve().parents[1]",
     "ROOT = SKILL"),
    ("adapters/inbound/contract/test_bc_artifact_share.py",
     "ROOT = Path(__file__).resolve().parents[4]",
     "ROOT = SKILL"),
    ("adapters/inbound/contract/test_deployed_gate.py",
     "ROOT = Path(__file__).resolve().parents[4]",
     "ROOT = SKILL"),
    ("adapters/inbound/contract/test_comment_entry_contract.py",
     "SKILL = Path(__file__).resolve().parents[4]",
     ""),
    ("browser/contract/test_browser_shipping_contract.py",
     "SKILL = Path(__file__).resolve().parents[3]",
     ""),
]

for rel, old, new in REPLACEMENTS:
    p = TESTS / rel
    t = p.read_text(encoding="utf-8")
    if old not in t:
        raise SystemExit(f"{rel} に見つかりません: {old}")
    t = t.replace(old, new, 1) if new else t.replace(old + "\n", "", 1)
    # conftest から受け取る
    if "from conftest import SKILL" not in t:
        m = re.search(r"^from pathlib import Path$", t, re.M)
        if m:
            t = t[:m.end()] + "\n\nfrom conftest import SKILL" + t[m.end():]
        else:
            raise SystemExit(f"{rel}: 取り込みを差し込む場所が見つかりません")
    p.write_text(t, encoding="utf-8")
    print("揃えた:", rel)

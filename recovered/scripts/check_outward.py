import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path("lambda/admin_api").resolve()))
from adapters.inbound.admin_api import _outward
from application.usecases.read_comments import CommentEntry, Comments
got = _outward(Comments(artifact_id="aaaaaaaa", unreadable=0, comments=(
    CommentEntry(id="1700000001-abcd1234", kind="comment", author="田中",
                 body="本文", posted_at="2026-08-09", verdict="approve",
                 parent_id=None),)))
print(json.dumps(got, ensure_ascii=False, indent=1))
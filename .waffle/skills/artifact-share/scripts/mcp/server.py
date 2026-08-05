#!/usr/bin/env python3
"""招かれた投稿者として、手元の道具から公開と管理を行うための受け口。

環境を作るCLI（scripts/artifactshare.py）とは、動く資格が違う。あちらはクラウドの
権限で動き、だから管理操作を持たない——持たせると「招かれた者だけが公開できる」
という前提が、権限を持つ人の手元で成り立たなくなる。こちらは合言葉で本人確認を
通り、招かれた投稿者としてできることだけを行う。関門は画面と同じで、そこを通る
窓口が1つ増えるだけ。

だからここにクラウドの権限を使う操作を足してはいけない。足した時点で、上の前提が
崩れる。

居場所と本人確認の材料は、環境変数から受け取る:
  ARTIFACTSHARE_DOMAIN    管理画面の居場所（例: admin.example.com）
  ARTIFACTSHARE_USER      招かれたときの宛先
  ARTIFACTSHARE_PASSWORD  自分で決めた合言葉

region と利用者プールの識別子は環境変数に持たない。構築時に置かれた
admin/config.json を読む——画面が読んでいるのと同じもので、二重に持つと
作り直したときに片方だけ古くなる。

初めて入るときの合言葉の決め直しは、ここでは行わない。画面で済ませてから使う
（決め直しの経路を2つ持つと、どちらが正かが分からなくなる）。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


class ToolError(Exception):
    """道具を呼ぶ前に分かった誤り。送らずにここで止める。"""


# 道具の名前と、その行き先・受け取る引数。
#
# 表にしてあるのは、受け口の経路表と同じ理由による。どれにも当たらなかったときの
# 行き先を持たせない。道具を1つ増やして行き先を書き忘れると、その道具は黙って
# 別の操作を呼ぶ——表であれば、行き先の無い道具はここで落ちる。
#
# 引数の「読む」は、手元のファイルを読んでその中身を別の欄として送ることを表す。
# 道具を呼ぶ側にHTMLの中身を持たせず、ファイルの場所だけを渡させるため。
TOOLS = {
    "publish": {
        "action": "publish",
        "description": "手元のHTMLを公開し、共有URLと閲覧トークンを受け取る。トークンはこのとき一度だけ示される",
        "args": [
            {"name": "path", "required": True, "reads_into": "html",
             "description": "公開するHTMLファイルの場所"},
            {"name": "displayName", "required": False,
             "description": "一覧で見分けるための題名。文書がmetaで名乗っていれば要らない"},
        ],
    },
    "list": {
        "action": "list",
        "description": "自分が公開したものの一覧を見る",
        "args": [],
    },
    "replace": {
        "action": "replace",
        "description": "公開済みのものの中身だけを入れ替える。共有URLも閲覧トークンも集まったコメントも保たれる",
        "args": [
            {"name": "artifactId", "required": True, "description": "入れ替える対象"},
            {"name": "path", "required": True, "reads_into": "html",
             "description": "新しいHTMLファイルの場所"},
        ],
    },
    "comments": {
        "action": "comments",
        "description": "寄せられたコメントを読む",
        "args": [{"name": "artifactId", "required": True, "description": "読む対象"}],
    },
    "export": {
        "action": "export",
        "description": "中身とコメントをまとめて手元へ持ち出す",
        "args": [{"name": "artifactId", "required": True, "description": "持ち出す対象"}],
    },
    "disable": {
        "action": "disable",
        "description": "開けない状態にする。中身もコメントも消えず、あとから再公開できる",
        "args": [{"name": "artifactId", "required": True, "description": "止める対象"}],
    },
    "enable": {
        "action": "enable",
        "description": "止めていたものを再び開けるようにする",
        "args": [{"name": "artifactId", "required": True, "description": "再開する対象"}],
    },
    "issue-token": {
        "action": "issue-token",
        "description": "渡す相手ごとに閲覧トークンを発行する。値はこのとき一度だけ示される",
        "args": [
            {"name": "artifactId", "required": False, "description": "共有アーティファクトを対象にするとき"},
            {"name": "projectId", "required": False, "description": "プロジェクトを対象にするとき"},
            {"name": "name", "required": True, "description": "どの配布先のものかを表す短い名前"},
            {"name": "ttl", "required": False, "description": "期限までの秒数"},
        ],
    },
    "view-tokens": {
        "action": "view-tokens",
        "description": "いま誰に見せているかを確かめる。閲覧トークンそのものの値は返らない",
        "args": [
            {"name": "artifactId", "required": False, "description": "共有アーティファクトを対象にするとき"},
            {"name": "projectId", "required": False, "description": "プロジェクトを対象にするとき"},
        ],
    },
    "revoke-token": {
        "action": "revoke-token",
        "description": "閲覧トークン1本を使えなくする。同じ対象の他の閲覧トークンには及ばない",
        "args": [
            {"name": "artifactId", "required": False, "description": "共有アーティファクトを対象にするとき"},
            {"name": "projectId", "required": False, "description": "プロジェクトを対象にするとき"},
            {"name": "tokenId", "required": True, "description": "無効にする閲覧トークン"},
        ],
    },
    "projects": {
        "action": "projects",
        "description": "プロジェクトの一覧を見る",
        "args": [],
    },
    "create-project": {
        "action": "create-project",
        "description": "複数の共有アーティファクトをまとめて見せる場を作る",
        "args": [
            {"name": "displayName", "required": True, "description": "プロジェクトの題名"},
            {"name": "scope", "required": True, "description": "shared（招かれた投稿者なら誰でも出し入れできる）か personal（持ち主だけ）"},
            {"name": "projectKey", "required": False, "description": "手元のフォルダと結びつけるための短い名前"},
        ],
    },
    "assign": {
        "action": "assign",
        "description": "共有アーティファクトをプロジェクトへ入れる",
        "args": [
            {"name": "artifactId", "required": True, "description": "入れる対象"},
            {"name": "projectId", "required": True, "description": "入れる先"},
        ],
    },
    "unassign": {
        "action": "unassign",
        "description": "共有アーティファクトをプロジェクトから出す",
        "args": [
            {"name": "artifactId", "required": True, "description": "出す対象"},
            {"name": "projectId", "required": True, "description": "出す先"},
        ],
    },
}


def build_body(name: str, arguments: dict) -> dict:
    """道具の呼び出しを、管理APIへ送る中身へ組み立てる。

    表に無い欄は落とす。渡されなかった任意の欄も落とす——空文字を送ると、受け口が
    「空の名前を指定された」と受け取ってしまい、指定しなかったことと区別できない。
    """
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolError(f"その道具はありません: {name}")

    body = {"action": tool["action"]}
    for spec in tool["args"]:
        value = arguments.get(spec["name"])
        if value in (None, ""):
            if spec["required"]:
                raise ToolError(f"{spec['name']} が要ります（{name}）")
            continue
        if spec.get("reads_into"):
            path = Path(str(value))
            if not path.is_file():
                raise ToolError(f"ファイルが見つかりません: {path}")
            body[spec["reads_into"]] = path.read_text(encoding="utf-8")
        else:
            body[spec["name"]] = value
    return body


def tool_list() -> list[dict]:
    """道具の一覧。表から導くのは、呼べるのに説明が無い道具を作らないため。"""
    return [
        {
            "name": name,
            "description": tool["description"],
            "inputSchema": {
                "type": "object",
                "properties": {
                    spec["name"]: {"type": "string", "description": spec["description"]}
                    for spec in tool["args"]
                },
                "required": [s["name"] for s in tool["args"] if s["required"]],
            },
        }
        for name, tool in TOOLS.items()
    ]


def handle(request: dict, call) -> dict:
    """手続きを1件処理する。送信の口は外から受け取る（ここは通信を知らない）。"""
    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        return _ok(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "artifact-share", "version": "1"},
        })
    if method == "tools/list":
        return _ok(request_id, {"tools": tool_list()})
    if method == "tools/call":
        params = request.get("params") or {}
        try:
            body = build_body(params.get("name", ""), params.get("arguments") or {})
            result = call(body)
        except ToolError as e:
            return _ok(request_id, {"content": [{"type": "text", "text": str(e)}],
                                    "isError": True})
        except Exception as e:  # 送った先での失敗も、道具の答えとして返す
            return _ok(request_id, {"content": [{"type": "text", "text": str(e)}],
                                    "isError": True})
        return _ok(request_id, {
            "content": [{"type": "text",
                         "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        })

    return {"jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32601, "message": f"知らない手続きです: {method}"}}


def _ok(request_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


# ── 外との接続 ────────────────────────────────────────

def _get_json(url: str) -> dict:  # pragma: no cover - 実際の通信
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict, headers: dict) -> dict:  # pragma: no cover
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode("utf-8", "replace")) from e


def _identify(domain: str, user: str, password: str) -> str:  # pragma: no cover
    """合言葉で本人確認を通り、証明を受け取る。"""
    config = _get_json(f"https://{domain}/admin/config.json")
    answer = _post_json(
        f"https://cognito-idp.{config['region']}.amazonaws.com/",
        {"AuthFlow": "USER_PASSWORD_AUTH", "ClientId": config["clientId"],
         "AuthParameters": {"USERNAME": user, "PASSWORD": password}},
        {"content-type": "application/x-amz-json-1.1",
         "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth"},
    )
    if answer.get("ChallengeName"):
        raise RuntimeError(
            "合言葉の決め直しが残っています。先に管理画面で決めてから使ってください。")
    return answer["AuthenticationResult"]["IdToken"]


def _connection():  # pragma: no cover - 結線だけ
    """送信の口を組み立てる。証明は最初の呼び出しのときに取り、以後は使い回す。"""
    domain = os.environ["ARTIFACTSHARE_DOMAIN"]
    user = os.environ["ARTIFACTSHARE_USER"]
    password = os.environ["ARTIFACTSHARE_PASSWORD"]
    held = {}

    def call(body: dict) -> dict:
        if "token" not in held:
            held["token"] = _identify(domain, user, password)
        return _post_json(f"https://{domain}/api", body,
                          {"content-type": "application/json",
                           "x-id-token": held["token"]})

    return call


def main() -> None:  # pragma: no cover - 読み書きの往復だけ
    call = _connection()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if request.get("id") is None and "method" in request:
            continue  # 答えを求めない知らせには答えない
        sys.stdout.write(json.dumps(handle(request, call), ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

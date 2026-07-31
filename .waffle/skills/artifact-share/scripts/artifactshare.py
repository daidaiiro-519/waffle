#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3"]
# ///
"""artifactshare.py — 共有する環境を用意し、手入れするCLI。

担うのは環境そのものの操作だけで、公開したあとの管理操作は持たない。
一覧・差し替え・トークンの再発行・公開停止・再開・プロジェクトの管理は、
Cognitoでログインした管理画面から行う。

管理操作をこちらにも持たせると、AWSの権限を持つ人の手元では「招かれた者だけが
公開できる」という前提が成り立たなくなり、同じ操作に入口が2つできる。
入口をひとつに保つため、ここでは扱わない。

使い方:
  artifactshare init
      環境を作る。作成後に管理画面のURLと、次にすることを表示する。

  artifactshare update-function
      閲覧の関門（CloudFront Functions）・管理の受け口（Lambda）・
      管理画面に、手元のソースを反映する。init のあとに必ず1回実行する。

  artifactshare invite <メールアドレス>
      公開できる人を招く。仮のパスワードが本人宛に届く。
      2人目以降は管理画面からも招けるので、ここで招くのは最初の1人でよい。

  artifactshare grant-admin <メールアドレス>
      その人を管理者にする。管理者は全員の共有アーティファクトを手入れでき、
      投稿者を出し入れできる。管理者を増やす操作だけは、AWSの権限を持つ人の
      手元に残してある（管理者が自分でさらに管理者を作れると、招かれた人の
      うち誰が最終的な責任を負うのかが辿れなくなるため）。

  artifactshare status
      いまの環境の状態（URL・招かれている人）を表示する。

  artifactshare destroy
      環境を消す。中身もコメントも消えるため、確認を求める。
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
DEFAULT_STACK = "artifact-share"


def _cfn(region: str | None):
    import boto3
    return boto3.client("cloudformation", region_name=region)


def _outputs(stack: str, region: str | None) -> dict:
    """作った環境が返す値（URL・識別子など）を取り出す。"""
    try:
        stacks = _cfn(region).describe_stacks(StackName=stack)["Stacks"]
    except Exception:
        print(f"環境（{stack}）が見つかりません。先に init を実行してください。",
              file=sys.stderr)
        raise SystemExit(1)
    return {o["OutputKey"]: o["OutputValue"] for o in stacks[0].get("Outputs", [])}


# ── 環境を作る・消す ────────────────────────────────────

def init(stack: str, region: str | None) -> None:
    import boto3

    template = (SKILL / "infra" / "cloudformation.yaml").read_text(encoding="utf-8")
    client = _cfn(region)

    # 保管の名前は全アカウントで一意である必要があるため、
    # アカウントと地域を混ぜて衝突しないようにする
    session = boto3.Session(region_name=region)
    account = session.client("sts").get_caller_identity()["Account"]
    suffix = f"{account}-{session.region_name}"

    print(f"環境を作っています（{stack}）。10分ほどかかります。")
    client.create_stack(
        StackName=stack,
        TemplateBody=template,
        Parameters=[
            {"ParameterKey": "BucketName", "ParameterValue": f"{stack}-{suffix}"},
            {"ParameterKey": "LogBucketName", "ParameterValue": f"{stack}-logs-{suffix}"},
        ],
        Capabilities=["CAPABILITY_IAM"],
    )
    client.get_waiter("stack_create_complete").wait(StackName=stack)

    out = _outputs(stack, region)
    print("\n用意できました。")
    print(f"  管理画面  : https://{out.get('AdminDomain', '')}/")
    print(f"  閲覧の入口: https://{out.get('ViewerDomain', '')}/")
    print("\n続けて次の2つを行ってください。")
    print("  1. artifactshare update-function    関門と受け口に中身を入れる")
    print("  2. artifactshare grant-admin <メール>  最初の管理者を決める")
    print("\nこの2つを省くと、管理画面を開いてもログインできず、"
          "共有URLもすべて開けないままになります。")


def destroy(stack: str, region: str | None) -> None:
    out = _outputs(stack, region)
    print(f"環境（{stack}）を消します。")
    print(f"  管理画面: https://{out.get('AdminDomain', '')}/")
    print("\n公開したものも、集まったコメントも、すべて消えます。元には戻せません。")
    if input(f"消してよければ環境の名前を入力してください（{stack}）: ").strip() != stack:
        print("やめました。")
        return

    bucket = out.get("BucketNameOut", "")
    if bucket:
        print(f"保管の中身を空にしています（{bucket}）…")
        subprocess.run(["aws", "s3", "rm", f"s3://{bucket}", "--recursive"], check=False)

    client = _cfn(region)
    client.delete_stack(StackName=stack)
    client.get_waiter("stack_delete_complete").wait(StackName=stack)
    print("消しました。")


# ── 公開できる人を招く ──────────────────────────────────

def invite(email: str, stack: str, region: str | None) -> None:
    import boto3

    out = _outputs(stack, region)
    boto3.client("cognito-idp", region_name=region).admin_create_user(
        UserPoolId=out["UserPoolId"],
        Username=email,
        UserAttributes=[{"Name": "email", "Value": email},
                        {"Name": "email_verified", "Value": "true"}],
        DesiredDeliveryMediums=["EMAIL"],
    )
    print(f"{email} を招きました。仮のパスワードが本人宛に届きます。")
    print(f"管理画面: https://{out.get('AdminDomain', '')}/")


def grant_admin(email: str, stack: str, region: str | None) -> None:
    """その人を管理者にする。招かれていなければ先に招く。"""
    import boto3

    out = _outputs(stack, region)
    idp = boto3.client("cognito-idp", region_name=region)
    pool = out["UserPoolId"]

    try:
        idp.admin_get_user(UserPoolId=pool, Username=email)
    except idp.exceptions.UserNotFoundException:
        print(f"{email} はまだ招かれていません。先に招きます。")
        invite(email, stack, region)

    idp.admin_add_user_to_group(UserPoolId=pool, Username=email,
                                GroupName="administrators")
    print(f"{email} を管理者にしました。")
    print("管理者は全員の共有アーティファクトを一覧・公開停止・再発行でき、"
          "投稿者を出し入れできます。")
    print("他人が公開したものの中身の差し替えだけはできません。")


# ── 手元のソースを反映する ──────────────────────────────

def update_function(stack: str, region: str | None) -> None:
    import boto3

    out = _outputs(stack, region)

    # 閲覧の関門。CloudFront Functions は us-east-1 でのみ扱える
    gate = (SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js") \
        .read_text(encoding="utf-8")
    cf = boto3.client("cloudfront", region_name="us-east-1")
    name = out.get("ViewerTokenGateFunctionName", f"{stack}-viewer-token-gate")
    etag = cf.describe_function(Name=name)["ETag"]
    etag = cf.update_function(
        Name=name, IfMatch=etag,
        FunctionConfig={"Comment": "viewer token gate", "Runtime": "cloudfront-js-2.0"},
        FunctionCode=gate.encode("utf-8"),
    )["ETag"]
    cf.publish_function(Name=name, IfMatch=etag)
    print("閲覧の関門を反映しました。")

    # 管理の受け口
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted((SKILL / "lambda" / "admin_api").glob("*.py")):
            zf.write(path, path.name)
        # 閲覧画面の雛形は公開のたびに読むため、受け口に同梱する
        zf.write(SKILL / "references" / "templates" / "share-wrapper.html",
                 "share-wrapper.html")

    boto3.client("lambda", region_name=region).update_function_code(
        FunctionName=out.get("AdminApiFunctionName", f"{stack}-admin-api"),
        ZipFile=buffer.getvalue(),
    )
    print("管理の受け口を反映しました。")

    _put_admin_app(out, region)
    print("管理画面を反映しました。")
    print("\n行き渡るまで数十秒かかります。")


def _put_admin_app(out: dict, region: str | None) -> None:
    """管理画面と、その設定を置く。

    設定を別ファイルにするのは、環境ごとに変わる値（受け口の居場所・
    利用者プールの識別子）を画面の中に焼き込まないため。画面は
    どの環境でも同じものを置ける。
    """
    import boto3

    s3 = boto3.client("s3", region_name=region)
    bucket = out["BucketNameOut"]

    app = (SKILL / "references" / "templates" / "upload-app.html") \
        .read_text(encoding="utf-8")
    s3.put_object(Bucket=bucket, Key="admin/index.html",
                  Body=app.encode("utf-8"), ContentType="text/html; charset=utf-8")

    session = boto3.Session(region_name=region)
    config = {
        "region": session.region_name,
        "apiUrl": out["AdminApiUrl"],
        "clientId": out["UserPoolClientId"],
        "viewerDomain": out["ViewerDomain"],
    }
    s3.put_object(Bucket=bucket, Key="admin/config.json",
                  Body=json.dumps(config, ensure_ascii=False).encode("utf-8"),
                  ContentType="application/json")


def status(stack: str, region: str | None) -> None:
    import boto3

    out = _outputs(stack, region)
    invited = boto3.client("cognito-idp", region_name=region) \
        .list_users(UserPoolId=out["UserPoolId"], Limit=60)["Users"]

    print(f"環境      : {stack}")
    print(f"管理画面   : https://{out.get('AdminDomain', '')}/")
    print(f"閲覧の入口 : https://{out.get('ViewerDomain', '')}/")
    print(f"招かれた人 : {len(invited)}人")
    for user in invited:
        print(f"  - {user['Username']}（{user['UserStatus']}）")


# ── 入り口 ──────────────────────────────────────────────

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="artifactshare", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--stack", default=DEFAULT_STACK, help="環境の名前")
    parser.add_argument("--region", default=None, help="地域")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="環境を作る")
    sub.add_parser("destroy", help="環境を消す")
    sub.add_parser("update-function", help="手元のソースを反映する")
    sub.add_parser("status", help="環境の状態を表示する")
    sub.add_parser("invite", help="公開できる人を招く") \
       .add_argument("email", help="招く人のメールアドレス")
    sub.add_parser("grant-admin", help="その人を管理者にする") \
       .add_argument("email", help="管理者にする人のメールアドレス")

    args = parser.parse_args(argv)
    {
        "init": lambda: init(args.stack, args.region),
        "destroy": lambda: destroy(args.stack, args.region),
        "update-function": lambda: update_function(args.stack, args.region),
        "status": lambda: status(args.stack, args.region),
        "invite": lambda: invite(args.email, args.stack, args.region),
        "grant-admin": lambda: grant_admin(args.email, args.stack, args.region),
    }[args.command]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

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
      閲覧ゲート（CloudFront Functions）・管理API（Lambda）・
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
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# 保管への書き込みで既定のチェックサム方式が追加の部品を要求するため、
# 必要なときだけ計算させる（実行環境に部品が無くても動くようにする）
os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")

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
    print("  1. artifactshare update-function    閲覧ゲートと管理APIに中身を入れる")
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
    # 宛先で入る設定のため、ここで渡す宛先は入り口の名前として使われ、
    # 名簿の中では別の識別子が振られる
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

# 閲覧ゲートに置けるコードの上限。超えると配置そのものが拒まれる
GATE_LIMIT = 10 * 1024


def _lean(source: str) -> str:
    """注釈と空行を落とす。

    閲覧ゲートは置けるコードの大きさに上限があり、日本語の注釈を含めると
    超える。読める形は手元に残し、置くときだけ落とす。行の途中にある注釈は
    触らない（文字列の中の // を誤って落とさないため）。
    """
    out, in_block = [], False
    for line in source.splitlines():
        stripped = line.strip()
        if in_block:
            if "*/" in stripped:
                in_block = False
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block = True
            continue
        if stripped.startswith("//") or not stripped:
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def update_function(stack: str, region: str | None) -> None:
    import boto3

    out = _outputs(stack, region)

    # 閲覧ゲート。CloudFront Functions は us-east-1 でのみ扱える
    gate = _lean((SKILL / "infra" / "cloudfront-function" / "viewer-token-gate.js")
                 .read_text(encoding="utf-8"))
    size = len(gate.encode("utf-8"))
    if size > GATE_LIMIT:
        print(f"閲覧ゲートが大きすぎます（{size} / {GATE_LIMIT} バイト）。"
              f"{size - GATE_LIMIT} バイト減らしてください。", file=sys.stderr)
        raise SystemExit(1)
    print(f"閲覧ゲート: {size} / {GATE_LIMIT} バイト（残り {GATE_LIMIT - size}）")
    cf = boto3.client("cloudfront", region_name="us-east-1")
    name = out.get("ViewerTokenGateFunctionName", f"{stack}-viewer-token-gate")
    described = cf.describe_function(Name=name)
    # 紐付けは毎回こちらで組み立てる。いまある設定を引き継ぐ形にすると、
    # 一度落ちたときにそのまま落ちたままになる。トークンの保管との
    # 紐付けが無いと、閲覧ゲートは動かず閲覧がすべて止まる（実地で確かめた）
    etag = cf.update_function(
        Name=name, IfMatch=described["ETag"],
        FunctionConfig={
            "Comment": "viewer token gate",
            "Runtime": "cloudfront-js-2.0",
            "KeyValueStoreAssociations": {
                "Quantity": 1,
                "Items": [{"KeyValueStoreARN": out["TokenStoreArn"]}],
            },
        },
        FunctionCode=gate.encode("utf-8"),
    )["ETag"]
    cf.publish_function(Name=name, IfMatch=etag)
    print("閲覧ゲートを反映しました。")

    # 管理API
    extra = _fetch_signing_parts()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted((SKILL / "lambda" / "admin_api").glob("*.py")):
            zf.write(path, path.name)
        for path in sorted(extra.rglob("*")):
            if path.is_file():
                zf.write(path, str(path.relative_to(extra)))
        # 閲覧画面とプロジェクトの一覧ページの雛形は、公開や作成のたびに
        # 読むため、管理APIに同梱する
        for name in ("share-wrapper.html", "project-page.html"):
            zf.write(SKILL / "references" / "templates" / name, name)

    boto3.client("lambda", region_name=region).update_function_code(
        FunctionName=out.get("AdminApiFunctionName", f"{stack}-admin-api"),
        ZipFile=buffer.getvalue(),
    )
    print("管理APIを反映しました。")

    _put_admin_app(out, region)
    print("管理画面を反映しました。")

    count = _put_project_pages(out, region)
    if count:
        print(f"プロジェクトの一覧ページを{count}件置き直しました。")
    print("\n行き渡るまで数十秒かかります。")


def _fetch_signing_parts() -> Path:
    """トークンの保管へ書くのに要る署名の部品を集める。

    CloudFront KeyValueStore のAPIは、複数の地域をまたぐ形の署名を使う。
    それを組み立てる部品は実行環境に入っておらず、無いと書き込みが
    「追加の部品が要る」として失敗する（実地で確かめた）。

    公開は保管への配置がすべて済んでから閲覧トークンを書く順序なので、
    ここが失敗すると、置かれたファイルは残るのに誰も開けない状態になる。
    """
    target = Path(tempfile.mkdtemp(prefix="artifactshare-parts-"))
    # 実行する側の環境ではなく、管理APIが動く環境に合う形のものを集める
    attempts = [
        ["uv", "pip", "install", "--quiet", "--target", str(target),
         "--python-platform", "x86_64-manylinux2014", "--python-version", "3.12",
         "--only-binary", ":all:", "awscrt"],
        [sys.executable, "-m", "pip", "install", "--quiet", "--target", str(target),
         "--platform", "manylinux2014_x86_64", "--python-version", "3.12",
         "--only-binary=:all:", "awscrt"],
    ]
    for command in attempts:
        try:
            subprocess.run(command, check=True, capture_output=True)
            return target
        except (OSError, subprocess.CalledProcessError):
            continue
    print("署名の部品を集められませんでした。uv か pip が必要です。", file=sys.stderr)
    raise SystemExit(1)


def _put_project_pages(out: dict, region: str | None) -> int:
    """既にあるプロジェクトの一覧ページを、いまの雛形で置き直す。

    雛形はどのプロジェクトでも同じものなので、直したときは全件へ行き渡らせる
    必要がある。中身（index.json）は触らない——そちらは所属が変わったときに
    管理APIが書き直しており、ここで上書きすると新しいものを古いもので潰す。
    """
    import boto3

    s3 = boto3.client("s3", region_name=region)
    bucket = out["BucketNameOut"]
    page = (SKILL / "references" / "templates" / "project-page.html") \
        .read_text(encoding="utf-8")

    count, token = 0, None
    while True:
        kw = {"Bucket": bucket, "Prefix": "projects/"}
        if token:
            kw["ContinuationToken"] = token
        res = s3.list_objects_v2(**kw)
        for obj in res.get("Contents", []):
            project_id = obj["Key"].removeprefix("projects/").removesuffix(".json")
            if not project_id:
                continue
            s3.put_object(
                Bucket=bucket, Key=f"proj/{project_id}/index.html",
                Body=page.replace("{{プロジェクトID}}", project_id).encode("utf-8"),
                ContentType="text/html; charset=utf-8", ChecksumAlgorithm="CRC32")
            count += 1
        token = res.get("NextContinuationToken")
        if not token:
            return count


def _put_admin_app(out: dict, region: str | None) -> None:
    """管理画面と、その設定を置く。

    設定を別ファイルにするのは、環境ごとに変わる値（管理APIの居場所・
    利用者プールの識別子）を画面の中に焼き込まないため。画面は
    どの環境でも同じものを置ける。
    """
    import boto3

    s3 = boto3.client("s3", region_name=region)
    bucket = out["BucketNameOut"]

    app = (SKILL / "references" / "templates" / "upload-app.html") \
        .read_text(encoding="utf-8")
    s3.put_object(Bucket=bucket, Key="admin/index.html",
                  Body=app.encode("utf-8"), ContentType="text/html; charset=utf-8",
                  ChecksumAlgorithm="CRC32")

    session = boto3.Session(region_name=region)
    # 管理APIの居場所は入れない。画面は同じ出所の /api を呼ぶため
    config = {
        "region": session.region_name,
        "clientId": out["UserPoolClientId"],
        "viewerDomain": out["ViewerDomain"],
    }
    s3.put_object(Bucket=bucket, Key="admin/config.json",
                  Body=json.dumps(config, ensure_ascii=False).encode("utf-8"),
                  ContentType="application/json", ChecksumAlgorithm="CRC32")


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

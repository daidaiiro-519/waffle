#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3", "awscrt"]
# ///
"""ds.py — design-share 統一CLI（Python版。common.sh〜galleries.sh等の全シェルスクリプトを統合）

合意事項（このセッションでのbash→Python移行の理由）:
  - 各シェルスクリプトは元々JSON/ロジック処理のほぼ全てをpython3 -c/heredocへ委譲しており、
    bashの脆弱なエラーハンドリングモデル自体が今回発覚した2件のバグ（KVSエラーの握りつぶし、
    `if VAR=$(cmd); then` のPOSIX終了ステータス仕様による誤り伝播消失）の温床になっていた。
  - console_server.pyと同じ基盤（uv run --script + PEP723 + boto3/awscrt）に統一する。

使い方:
  uv run ds.py init                          AWS環境を対話式に用意する（既存スタック利用 or 新規構築 → design-share.env生成 → edge-gate反映）
  uv run ds.py destroy                       AWS環境（CloudFormationスタック）を対話式に削除する（initの対）
  uv run ds.py list                          公開中/無効化済みパターンの一覧
  uv run ds.py deploy <html> "<表示名>"      パターンをデプロイ（slug＋トークン発行）
  uv run ds.py deploy --design <DESIGN.md> <spec.html> "<名>"  DESIGN.md視覚スペックシートをレビュー用に公開
  uv run ds.py redeploy <slug> <html>        既存パターンの内容だけを差し替える（URL・トークン・既存コメントは維持）
  uv run ds.py redeploy --design <DESIGN.md> <slug> <spec.html>  DESIGN.mdレビュー版のDESIGN.md本体も同様に差し替える
  uv run ds.py confirm-design <slug> [--to <dir>]  レビュー済みDESIGN.mdを正式な配置場所へ確定配置
                                              （同一プロジェクト内の既存の確定済みDESIGN.mdは自動的に確定解除される）
  uv run ds.py confirm <slug>                UIモックを確定（採用案にする）。DESIGN.mdと違い複数同時に確定していてよい
  uv run ds.py unconfirm <slug>              UIモックの確定を取り消す
  uv run ds.py export <slug> [outdir]        zipエクスポート（公開状態は変えない）
  uv run ds.py rotate <slug>                 トークン再発行（DISABLEDなら再公開）
  uv run ds.py disable <slug> [--no-export]  無効化（既定でエクスポート同伴）
  uv run ds.py rename <slug> "<新名>"        表示名のみ変更（slug・トークン・公開状態は不変）
  uv run ds.py console                       Web管理コンソールをlocalhostで起動
  uv run ds.py update-function               edge-gate.jsをCloudFront Functionへ反映
  uv run ds.py gallery <init|rotate|disable|url>  全体ギャラリー（共通トークンで全部入り）を管理
  uv run ds.py galleries <create|list|rotate|disable|delete|add|remove|set ...>  名前付きギャラリー（プロジェクト）を管理
                                              createは表示名の他に --key <プロジェクトキー> を取る（省略時は表示名から自動生成）
  uv run ds.py reconcile                     S3のmeta(真実源)からKVS投影(pg/status)・index.jsonを再生成
  uv run ds.py smoke                         実機スモークテスト（使い捨てパターンで往復検証）
"""
from __future__ import annotations

import datetime
import hashlib
import http.cookiejar
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import boto3
import botocore.exceptions

SCRIPT_DIR = Path(__file__).resolve().parent
MAX_PATTERN_GALLERIES = 3
GSLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- 設定読み込み -----------------------------------------------------------

def resolve_env_path() -> Path:
    return Path(os.environ.get("DESIGN_SHARE_ENV", str(Path.cwd() / "design-share.env"))).resolve()


def load_env(path: Path) -> dict:
    conf: dict[str, str] = {}
    if not path.is_file():
        return conf
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            if k.startswith("export "):  # `export AWS_PROFILE=dev` 形式に対応
                k = k[len("export "):].strip()
            conf[k] = v.strip()
    return conf


class Ctx:
    """common.sh が担っていた設定解決＋クライアント一式"""

    def __init__(self) -> None:
        self.env_path = resolve_env_path()
        if not self.env_path.is_file():
            die(
                f"error: 設定ファイルが見つかりません: {self.env_path}\n"
                "CloudFormationスタックのOutputsをもとに design-share.env を作成し、"
                "そのディレクトリで実行するか DESIGN_SHARE_ENV に絶対パスを設定してください。"
            )
        self.conf = load_env(self.env_path)
        for key in ("BUCKET", "DISTRIBUTION_DOMAIN", "KVS_ARN"):
            if not self.conf.get(key):
                die(f"error: design-share.env に {key} が必要です")
        self.bucket = self.conf["BUCKET"]
        self.domain = self.conf["DISTRIBUTION_DOMAIN"]
        self.kvs_arn = self.conf["KVS_ARN"]
        self.function_name = self.conf.get("FUNCTION_NAME", "")
        for k in ("AWS_PROFILE", "AWS_REGION", "AWS_DEFAULT_REGION"):
            if self.conf.get(k):
                os.environ.setdefault(k, self.conf[k])
        session = boto3.Session(
            profile_name=self.conf.get("AWS_PROFILE") or None,
            region_name=self.conf.get("AWS_REGION") or self.conf.get("AWS_DEFAULT_REGION") or None,
        )
        self.s3 = session.client("s3")
        self.kvs = session.client("cloudfront-keyvaluestore")
        self.cf = session.client("cloudfront")


# --- KeyValueStore helpers ---------------------------------------------------
# token:{slug} が唯一の状態キー: 通常値=現在有効なトークン / "DISABLED"=無効化済み

def kvs_etag(ctx: Ctx) -> str:
    return ctx.kvs.describe_key_value_store(KvsARN=ctx.kvs_arn)["ETag"]


def kvs_put(ctx: Ctx, key: str, value: str) -> None:
    ctx.kvs.put_key(KvsARN=ctx.kvs_arn, Key=key, Value=value, IfMatch=kvs_etag(ctx))


def kvs_get(ctx: Ctx, key: str) -> str:
    # 「キーが無い」と「取得そのものに失敗した」を区別する。ResourceNotFoundExceptionのうち
    # メッセージが「No such Key exists」（未設定）だけを正常系として空文字を返し、
    # 「No such Key-Value-Store exists」（KVS_ARN誤り）等はそのまま伝播させる
    # （common.shのkvs_get()で踏んだ握りつぶし事故と同型のバグを再発させないため）
    try:
        return ctx.kvs.get_key(KvsARN=ctx.kvs_arn, Key=key).get("Value", "")
    except ctx.kvs.exceptions.ResourceNotFoundException as e:
        if "No such Key exists" in str(e):
            return ""
        raise


# --- S3 helpers ---------------------------------------------------------------

def s3_get_text(ctx: Ctx, key: str) -> str | None:
    try:
        return ctx.s3.get_object(Bucket=ctx.bucket, Key=key)["Body"].read().decode("utf-8")
    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None
        raise


def s3_put_text(ctx: Ctx, key: str, text: str, content_type: str = "application/json") -> None:
    ctx.s3.put_object(Bucket=ctx.bucket, Key=key, Body=text.encode("utf-8"), ContentType=content_type)


def s3_head_exists(ctx: Ctx, key: str) -> bool:
    try:
        ctx.s3.head_object(Bucket=ctx.bucket, Key=key)
        return True
    except botocore.exceptions.ClientError:
        return False


def list_keys(ctx: Ctx, prefix: str) -> list[str]:
    keys: list[str] = []
    paginator = ctx.s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=ctx.bucket, Prefix=prefix):
        keys.extend(o["Key"] for o in page.get("Contents", []))
    return keys


def _s3_delete_prefix(ctx: Ctx, prefix: str) -> None:
    keys = list_keys(ctx, prefix)
    for i in range(0, len(keys), 1000):
        batch = keys[i:i + 1000]
        if batch:
            ctx.s3.delete_objects(Bucket=ctx.bucket, Delete={"Objects": [{"Key": k} for k in batch]})


def _s3_download_prefix(ctx: Ctx, prefix: str, dest_dir: Path) -> int:
    keys = list_keys(ctx, prefix)
    dest_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for k in keys:
        rel = k[len(prefix):]
        if not rel:
            continue
        target = dest_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            ctx.s3.download_file(ctx.bucket, k, str(target))
            n += 1
        except botocore.exceptions.ClientError:
            continue
    return n


# --- meta helpers ---
# 真実源の割り当て（reconcile_projections がこの前提で投影を再生成する）:
#   秘密トークン         → KVS が権威（token:{slug} / g:{gslug} / project:token）。S3には残さない
#   構造・状態・名前・所属 → S3 の meta/{slug}.json が権威
#   投影(再生成可・非権威) → KVS pg:{slug}、gallery/index.json、g/*/index.json、token:のDISABLED overlay

def meta_write(ctx: Ctx, slug: str, name: str, status: str) -> bool:
    # 既存galleries[]の保持は、metaが「読めた」ときだけ行う。読めない場合:
    #   - オブジェクトが存在しない（新規デプロイ）→ galleries=[] で新規作成してよい
    #   - 存在するのに読めない（一時失敗）→ 上書きを中止（galleries[]の消失を防ぐ）
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if cur:
        try:
            base = json.loads(cur)
            if not isinstance(base, dict):
                base = {}
        except Exception:
            print(f"meta_write: 既存metaの解析に失敗したため上書きを中止: {slug}", file=sys.stderr)
            return False
    elif s3_head_exists(ctx, f"meta/{slug}.json"):
        print(f"meta_write: 既存metaが存在するのに読めなかったため上書きを中止（所属消失防止）: {slug}", file=sys.stderr)
        return False
    else:
        base = {}
    base.setdefault("galleries", [])
    base.update({"slug": slug, "name": name, "status": status, "updatedAt": now_iso()})
    s3_put_text(ctx, f"meta/{slug}.json", json.dumps(base, ensure_ascii=False))
    return True


def meta_patch(ctx: Ctx, slug: str, patch: dict) -> bool:
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if not cur:
        print(f"meta_patch: metaが読めません: {slug}", file=sys.stderr)
        return False
    obj = json.loads(cur)
    if not isinstance(obj, dict):
        print(f"meta_patch: meta is not an object: {slug}", file=sys.stderr)
        return False
    obj.update(patch)
    obj["updatedAt"] = now_iso()
    s3_put_text(ctx, f"meta/{slug}.json", json.dumps(obj, ensure_ascii=False))
    return True


def meta_name(ctx: Ctx, slug: str) -> str:
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if not cur:
        return ""
    try:
        return json.loads(cur).get("name", "")
    except Exception:
        return ""


def meta_status(ctx: Ctx, slug: str) -> str:
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if not cur:
        return ""
    try:
        return json.loads(cur).get("status", "")
    except Exception:
        return ""


def new_token() -> str:
    return secrets.token_urlsafe(16)


def new_slug() -> str:
    return secrets.token_hex(8)


def new_gslug() -> str:
    return secrets.token_hex(6)


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.strip().lower())
    return s.strip("-") or "project"


# --- ギャラリー ---
# 全体ギャラリー: KVS project:token（値 or "DISABLED"）で入る全部入りランディング（/gallery/）。
# 名前付きギャラリー（カテゴリ）: KVS g:{gslug}（値 or "DISABLED"）で入る /g/{gslug}/。所属はタグ式。

def gallery_enabled(ctx: Ctx) -> str:
    v = kvs_get(ctx, "project:token")
    return v if v and v not in ("DISABLED", "None") else ""


def gallery_meta_write(ctx: Ctx, gslug: str, name: str, project_key: str = "") -> None:
    # projectKey: ローカルのプロジェクトフォルダ名と照合するための半角キー（表示名とは別）。
    # コンソールはローカルフォルダ名でこれを検索し、ローカル/クラウドを紐付ける（論点6の最終合意）。
    s3_put_text(ctx, f"galleries/{gslug}.json",
                json.dumps({"gslug": gslug, "name": name, "projectKey": project_key, "updatedAt": now_iso()},
                           ensure_ascii=False))


def gallery_meta_get(ctx: Ctx, gslug: str) -> dict:
    cur = s3_get_text(ctx, f"galleries/{gslug}.json")
    if not cur:
        return {}
    try:
        obj = json.loads(cur)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def gallery_meta_name(ctx: Ctx, gslug: str) -> str:
    cur = s3_get_text(ctx, f"galleries/{gslug}.json")
    if not cur:
        return ""
    try:
        return json.loads(cur).get("name", "")
    except Exception:
        return ""


def pattern_galleries(ctx: Ctx, slug: str) -> list[str]:
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if not cur:
        return []
    try:
        return list(json.loads(cur).get("galleries", []) or [])
    except Exception:
        return []


def pattern_set_galleries(ctx: Ctx, slug: str, gslugs: list[str]) -> bool:
    gslugs = [g for g in gslugs if g]
    if len(gslugs) > MAX_PATTERN_GALLERIES:
        print(f"所属カテゴリは最大 {MAX_PATTERN_GALLERIES} 件までです（指定: {len(gslugs)} 件）: {slug}", file=sys.stderr)
        return False
    cur = s3_get_text(ctx, f"meta/{slug}.json")
    if not cur:
        print(f"meta not found or empty: {slug}", file=sys.stderr)
        return False
    meta = json.loads(cur)
    meta["galleries"] = gslugs
    s3_put_text(ctx, f"meta/{slug}.json", json.dumps(meta, ensure_ascii=False))
    kvs_put(ctx, f"pg:{slug}", " ".join(gslugs))  # エッジのスコープ判定用の鏡像
    rebuild_gallery_index(ctx)
    return True


def slim(r: dict) -> dict:
    return {"slug": r.get("slug", ""), "name": r.get("name", ""),
            "status": r.get("status", "active"), "updatedAt": r.get("updatedAt", "")}


def rebuild_gallery_index(ctx: Ctx) -> None:
    metas = []
    for k in list_keys(ctx, "meta/"):
        txt = s3_get_text(ctx, k)
        if not txt:
            continue
        try:
            metas.append(json.loads(txt))
        except Exception:
            continue
    gals = []
    for k in list_keys(ctx, "galleries/"):
        txt = s3_get_text(ctx, k)
        if not txt:
            continue
        try:
            gals.append(json.loads(txt))
        except Exception:
            continue
    s3_put_text(ctx, "gallery/index.json", json.dumps([slim(r) for r in metas], ensure_ascii=False))
    for g in gals:
        gs = g.get("gslug", "")
        if not gs:
            continue
        items = [slim(r) for r in metas if gs in (r.get("galleries") or [])]
        s3_put_text(ctx, f"g/{gs}/index.json",
                    json.dumps({"name": g.get("name", ""), "gslug": gs, "items": items}, ensure_ascii=False))


def reconcile_projections(ctx: Ctx) -> None:
    n = 0
    warned = 0
    for k in list_keys(ctx, "meta/"):
        slug = Path(k).stem
        gl = pattern_galleries(ctx, slug)
        kvs_put(ctx, f"pg:{slug}", " ".join(gl))
        st = meta_status(ctx, slug)
        tok = kvs_get(ctx, f"token:{slug}")
        if st == "disabled":
            if tok != "DISABLED":
                kvs_put(ctx, f"token:{slug}", "DISABLED")
        elif tok == "DISABLED":
            print(f"  ⚠ {slug}: metaはactiveだがKVSがDISABLED。トークンは秘密でmetaから復元不可 → "
                  f"ds.py rotate {slug} で再発行を", file=sys.stderr)
            warned += 1
        n += 1
    rebuild_gallery_index(ctx)
    print(f"reconcile完了: {n}パターンの投影(pg:/index/status overlay)をmetaから再生成しました（要対応: {warned}件）。")


# --- パターン操作コア（CLIラッパーとsmokeテストの両方から呼ばれる） -------------

def deploy_pattern_core(ctx: Ctx, html_file: str, display_name: str,
                         type_: str = "mock", design_src: str | None = None) -> tuple[str, str, str]:
    if not Path(html_file).is_file():
        die(f"error: HTMLファイルが見つかりません: {html_file}")
    if type_ not in ("mock", "design-review"):
        die(f"error: --type は mock か design-review: {type_}")
    if design_src:
        if not Path(design_src).is_file():
            die(f"error: DESIGN.mdが見つかりません: {design_src}")
        type_ = "design-review"

    slug = new_slug()
    token = new_token()

    html_content = Path(html_file).read_text(encoding="utf-8")
    html = html_content.replace("{{スラッグ}}", slug)
    ctx.s3.put_object(Bucket=ctx.bucket, Key=f"p/{slug}/index.html",
                       Body=html.encode("utf-8"), ContentType="text/html; charset=utf-8")

    kvs_put(ctx, f"token:{slug}", token)
    meta_write(ctx, slug, display_name, "active")

    # sourceFile/sourceHash: ローカル/クラウドの同期状態をその場で判定するための手がかり
    # （論点6の最終合意。ローカルには紐付け専用ファイルを持たず、これだけで判定する）。
    # design-reviewはDESIGN.md本体を追跡対象にする（自動生成されるspec.htmlはビルド成果物のため対象外）。
    patch: dict = {}
    if design_src:
        design_bytes = Path(design_src).read_bytes()
        ctx.s3.upload_file(design_src, ctx.bucket, f"design/{slug}.md",
                            ExtraArgs={"ContentType": "text/markdown; charset=utf-8"})
        patch["type"] = type_
        patch["designSource"] = f"design/{slug}.md"
        patch["sourceFile"] = Path(design_src).name
        patch["sourceHash"] = hashlib.sha256(design_bytes).hexdigest()
    else:
        patch["sourceFile"] = f"mocks/{Path(html_file).name}"
        patch["sourceHash"] = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
    meta_patch(ctx, slug, patch)

    rebuild_gallery_index(ctx)  # ギャラリー集約インデックスを最新化
    return slug, token, type_


def redeploy_pattern_core(ctx: Ctx, slug: str, html_file: str, design_src: str | None = None) -> None:
    # deployは呼ぶたびに新しいslug（＝新しいURL）を発行するため、レビュー中に内容を直すたびに
    # コメントスレッドが途切れてしまう（旧slugのcomments/配下に取り残される）。redeployは既存の
    # slugのURL・トークン・comments/配下をそのまま維持し、p/{slug}/index.html の中身とsourceHash
    # だけを差し替える（論点: 同一URLでの反復レビューを成立させるための追加コマンド）。
    if not Path(html_file).is_file():
        die(f"error: HTMLファイルが見つかりません: {html_file}")
    if not meta_name(ctx, slug):
        die(f"error: パターンが見つかりません: {slug}")

    html_content = Path(html_file).read_text(encoding="utf-8")
    html = html_content.replace("{{スラッグ}}", slug)
    ctx.s3.put_object(Bucket=ctx.bucket, Key=f"p/{slug}/index.html",
                       Body=html.encode("utf-8"), ContentType="text/html; charset=utf-8")

    patch: dict = {}
    if design_src:
        if not Path(design_src).is_file():
            die(f"error: DESIGN.mdが見つかりません: {design_src}")
        design_bytes = Path(design_src).read_bytes()
        ctx.s3.upload_file(design_src, ctx.bucket, f"design/{slug}.md",
                            ExtraArgs={"ContentType": "text/markdown; charset=utf-8"})
        patch["designSource"] = f"design/{slug}.md"
        patch["sourceFile"] = Path(design_src).name
        patch["sourceHash"] = hashlib.sha256(design_bytes).hexdigest()
    else:
        patch["sourceFile"] = f"mocks/{Path(html_file).name}"
        patch["sourceHash"] = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
    meta_patch(ctx, slug, patch)


def export_pattern_core(ctx: Ctx, slug: str, outdir: str | Path) -> tuple[Path, int, int]:
    outdir = Path(outdir)
    with tempfile.TemporaryDirectory() as work_s:
        work = Path(work_s)
        pattern_count = _s3_download_prefix(ctx, f"p/{slug}/", work / "pattern")
        comment_count = _s3_download_prefix(ctx, f"comments/{slug}/", work / "comments")

        outdir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_path = outdir / f"design-share-{slug}-{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(work):
                for name in files:
                    full = Path(root) / name
                    z.write(full, full.relative_to(work))
    return zip_path, pattern_count, comment_count


def project_metas(ctx: Ctx, gslug: str) -> list[dict]:
    metas = []
    for k in list_keys(ctx, "meta/"):
        txt = s3_get_text(ctx, k)
        if not txt:
            continue
        try:
            m = json.loads(txt)
        except Exception:
            continue
        if gslug in (m.get("galleries") or []):
            metas.append(m)
    return metas


def export_project_core(ctx: Ctx, gslug: str, outdir: str | Path,
                         mock_slugs: list[str] | None = None) -> tuple[Path, dict]:
    """プロジェクト単位エクスポート（論点3の最終合意）: 確定済みDESIGN.md 1件＋指定したUIモック＋
    各パターンのコメントを1つのzipにまとめる。未確定のDESIGN.md案は対象にしない。
    mock_slugsを指定しなければ「確定済み」のモックだけを対象にする（コンソールの既定選択と揃える）。"""
    metas = project_metas(ctx, gslug)
    designs = [m for m in metas if m.get("type") == "design-review" and m.get("confirmedAt")]
    if not designs:
        die(f"error: このプロジェクトには確定済みのDESIGN.mdがありません: {gslug}")
    design = sorted(designs, key=lambda m: m.get("confirmedAt", ""), reverse=True)[0]

    mocks = [m for m in metas if m.get("type") != "design-review"]
    if mock_slugs is not None:
        wanted = set(mock_slugs)
        mocks = [m for m in mocks if m.get("slug") in wanted]
    else:
        mocks = [m for m in mocks if m.get("confirmed")]

    outdir = Path(outdir)
    with tempfile.TemporaryDirectory() as work_s:
        work = Path(work_s)
        dslug = design["slug"]
        _s3_download_prefix(ctx, f"p/{dslug}/", work / "design")
        _s3_download_prefix(ctx, f"comments/{dslug}/", work / "design" / "comments")
        for m in mocks:
            s = m["slug"]
            _s3_download_prefix(ctx, f"p/{s}/", work / "mocks" / s)
            _s3_download_prefix(ctx, f"comments/{s}/", work / "mocks" / s / "comments")

        outdir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_path = outdir / f"design-share-{gslug}-{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(work):
                for name in files:
                    full = Path(root) / name
                    z.write(full, full.relative_to(work))
    return zip_path, {"design": design["slug"], "mocks": [m["slug"] for m in mocks]}


def rotate_token_core(ctx: Ctx, slug: str) -> tuple[str, bool]:
    token = new_token()
    was = kvs_get(ctx, f"token:{slug}")
    kvs_put(ctx, f"token:{slug}", token)
    republished = False
    if was == "DISABLED":
        name = meta_name(ctx, slug) or slug
        meta_write(ctx, slug, name, "active")
        rebuild_gallery_index(ctx)  # 再公開をギャラリー一覧へ反映
        republished = True
    return token, republished


def invalidate_pattern_core(ctx: Ctx, slug: str, do_export: bool = True) -> None:
    # 「無効化したがエクスポートを忘れた」を構造的に防ぐため、既定でエクスポートを先に実行する
    if do_export:
        export_pattern_core(ctx, slug, "./exports")
    kvs_put(ctx, f"token:{slug}", "DISABLED")
    name = meta_name(ctx, slug) or slug
    meta_write(ctx, slug, name, "disabled")
    rebuild_gallery_index(ctx)  # 無効化をギャラリー一覧へ反映


def galleries_create_core(ctx: Ctx, name: str, project_key: str = "") -> tuple[str, str, str]:
    gslug = new_gslug()
    token = new_token()
    project_key = project_key or slugify(name)
    app_path = SCRIPT_DIR.parent / "references" / "templates" / "gallery-app.html"
    ctx.s3.put_object(Bucket=ctx.bucket, Key="gallery/app.html",
                       Body=app_path.read_bytes(), ContentType="text/html; charset=utf-8")
    gallery_meta_write(ctx, gslug, name, project_key)
    kvs_put(ctx, f"g:{gslug}", token)
    rebuild_gallery_index(ctx)
    return gslug, token, project_key


def find_gslug_by_project_key(ctx: Ctx, project_key: str) -> str | None:
    """ローカルのプロジェクトフォルダ名からクラウドのプロジェクト(gslug)を毎回その場で探す。
    ローカルには紐付け専用ファイルを一切持たない（論点6の最終合意）。"""
    for k in list_keys(ctx, "galleries/"):
        g = gallery_meta_get(ctx, Path(k).stem)
        if g.get("projectKey") == project_key:
            return g.get("gslug") or Path(k).stem
    return None


# --- CLIコマンド --------------------------------------------------------------

def cmd_list(ctx: Ctx, argv: list[str]) -> None:
    # 認証・権限エラーを「0件」と誤認しないよう、まずlistの成否を確認する
    try:
        keys = list_keys(ctx, "meta/")
    except botocore.exceptions.ClientError as e:
        print("パターン一覧の取得に失敗しました（認証・権限・バケット名を確認してください）:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(1)
    rows = []
    for k in keys:
        txt = s3_get_text(ctx, k)
        if not txt:
            continue
        try:
            rows.append(json.loads(txt))
        except Exception:
            continue
    if not rows:
        print("デプロイ済みパターンはありません。")
        return
    rows.sort(key=lambda r: r.get("updatedAt", ""), reverse=True)
    w = max((len(r.get("name", "")) for r in rows), default=0)
    for r in rows:
        mark = "公開中 " if r.get("status") == "active" else "無効化"
        print(f"[{mark}] {r.get('name', ''):<{w}}  slug={r.get('slug', '')}  updated={r.get('updatedAt', '')[:10]}")


def cmd_deploy(ctx: Ctx, argv: list[str]) -> None:
    type_ = "mock"
    design_src = None
    pos: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--type":
            if i + 1 >= len(argv):
                die("--type には値が必要です")
            type_ = argv[i + 1]
            i += 2
        elif a == "--design":
            if i + 1 >= len(argv):
                die("--design には値が必要です")
            design_src = argv[i + 1]
            i += 2
        else:
            pos.append(a)
            i += 1
    if len(pos) < 2:
        die("usage: deploy [--type mock|design-review] [--design <DESIGN.mdパス>] <html-file> <display-name>")
    html_file, display_name = pos[0], pos[1]

    slug, token, type_ = deploy_pattern_core(ctx, html_file, display_name, type_, design_src)

    print()
    label = f"デプロイ完了: {display_name}" + ("  [DESIGN.mdレビュー]" if type_ == "design-review" else "")
    print(label)
    print(f"  URL   : https://{ctx.domain}/p/{slug}/")
    print(f"  トークン: {token}")
    print()
    print("トークンはこの一度しか表示されません。URLとは別のチャネルで共有相手に渡してください。")
    print(f"紛失した場合は ds.py rotate {slug} で再発行できます。")
    if type_ == "design-review":
        print()
        print("これはDESIGN.mdのレビュー用スペックシートです。関係者のコメントで合意できたら、")
        print(f"  ds.py confirm-design {slug} [--to <配置先ディレクトリ>]")
        print("でDESIGN.mdを正式な配置場所（既定: ./DESIGN.md）へ配置してください。")
    print()
    print("補足: デプロイ直後の数十秒はエッジへのトークン伝播（KVSの結果整合）が済むまで")
    print("      403（無効化済みの表示）に見えることがあります。少し待ってから再読み込みしてください。")


def cmd_redeploy(ctx: Ctx, argv: list[str]) -> None:
    design_src = None
    pos: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--design":
            if i + 1 >= len(argv):
                die("--design には値が必要です")
            design_src = argv[i + 1]
            i += 2
        else:
            pos.append(a)
            i += 1
    if len(pos) < 2:
        die("usage: redeploy [--design <DESIGN.mdパス>] <slug> <html-file>")
    slug, html_file = pos[0], pos[1]
    require_pattern(slug)

    redeploy_pattern_core(ctx, slug, html_file, design_src)

    print()
    print(f"更新完了: {slug}")
    print(f"  URL: https://{ctx.domain}/p/{slug}/  （URL・トークン・既存コメントは変わりません）")
    print()
    print("補足: 反映は数秒〜数十秒かかる場合があります。少し待ってから再読み込みしてください。")


def supersede_confirmed_designs(ctx: Ctx, gslug: str, except_slug: str) -> list[str]:
    """1プロジェクトにつき確定済みDESIGN.mdは常に高々1つ、という制約を強制する（論点4の最終合意）。
    同一プロジェクト内の他の確定済みdesign-reviewパターンを確定解除する。UIモックの確定はこの対象外
    （supersedeしない。論点4で複数モックが同時に確定していてよいと合意したため）。"""
    superseded = []
    for k in list_keys(ctx, "meta/"):
        slug = Path(k).stem
        if slug == except_slug:
            continue
        txt = s3_get_text(ctx, k)
        if not txt:
            continue
        try:
            m = json.loads(txt)
        except Exception:
            continue
        if m.get("type") != "design-review":
            continue
        if gslug not in (m.get("galleries") or []):
            continue
        if not m.get("confirmedAt"):
            continue
        meta_patch(ctx, slug, {"confirmedAt": None, "confirmedTo": None})
        superseded.append(slug)
    return superseded


def cmd_confirm_design(ctx: Ctx, argv: list[str]) -> None:
    slug = None
    to_dir = "."
    do_export = True
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--to":
            if i + 1 >= len(argv):
                die("--to にはディレクトリが必要です")
            to_dir = argv[i + 1]
            i += 2
        elif a == "--no-export":
            do_export = False
            i += 1
        elif a.startswith("-"):
            die(f"error: 不明なオプション: {a}")
        else:
            slug = a
            i += 1
    if not slug:
        die("usage: confirm-design <slug> [--to <dir>] [--no-export]")

    meta_text = s3_get_text(ctx, f"meta/{slug}.json")
    if not meta_text:
        die(f"error: metaが読めません（slugを確認してください）: {slug}")
    meta = json.loads(meta_text)
    mtype = meta.get("type", "mock")
    msrc = meta.get("designSource", "")
    mname = (meta.get("name", "") or "-")
    if mtype != "design-review":
        die(f"error: このslugはDESIGN.mdレビューではありません（type={mtype}）。confirm-designの対象外です: {slug}")
    if not msrc:
        die(f"error: このレビューにはDESIGN.md本体が保存されていません（deploy時に --design を付けていない）: {slug}")

    content = s3_get_text(ctx, msrc)
    if content is None:
        die(f"error: DESIGN.md本体の取得に失敗: s3://{ctx.bucket}/{msrc}")
    if not content.strip():
        die(f"error: 取得したDESIGN.mdが空です: {msrc}")

    to_path = Path(to_dir)
    to_path.mkdir(parents=True, exist_ok=True)
    dest = to_path / "DESIGN.md"

    if dest.is_file():
        if dest.read_text(encoding="utf-8") == content:
            print(f"既存の {dest} は確定内容と同一でした（変更なし）。")
        else:
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            bak = dest.with_name(dest.name + f".bak-{stamp}")
            shutil.copy(dest, bak)
            print(f"既存の {dest} を {bak} に退避しました。")
    dest.write_text(content, encoding="utf-8")

    abs_dest = str(dest.resolve())
    meta_patch(ctx, slug, {"confirmedAt": now_iso(), "confirmedTo": abs_dest})

    galleries = meta.get("galleries") or []
    if galleries:
        superseded = supersede_confirmed_designs(ctx, galleries[0], except_slug=slug)
        if superseded:
            print(f"同一プロジェクト内の既存の確定済みDESIGN.mdを確定解除しました: {', '.join(superseded)}")

    print()
    print(f"確定しました: {mname}")
    print(f"  配置先: {abs_dest}")

    if do_export:
        print()
        print("レビューコメントを記録としてエクスポートします...")
        try:
            cmd_export(ctx, [slug])
        except SystemExit:
            print("（エクスポートはスキップされました）", file=sys.stderr)

    print()
    print("次のステップ:")
    print("  - このDESIGN.mdを単一の源として、対話でUIモックを生成できます（confirm-designはモックを生成しません）。")
    print(f"  - レビュー用スペックシート自体が不要になったら ds.py disable {slug} で公開を止められます（データは残ります）。")


def cmd_confirm_mock(ctx: Ctx, argv: list[str]) -> None:
    # UIモックの確定は「採用案にする」の意味で、DESIGN.mdと違いsupersedeしない
    # （同じプロジェクト内で複数のモックが同時に確定していてよい。論点4の最終合意）。
    if not argv:
        die("usage: confirm <slug>")
    slug = argv[0]
    meta_text = s3_get_text(ctx, f"meta/{slug}.json")
    if not meta_text:
        die(f"error: metaが読めません（slugを確認してください）: {slug}")
    meta = json.loads(meta_text)
    if meta.get("type") == "design-review":
        die(f"error: このslugはDESIGN.mdレビューです。確定には ds.py confirm-design を使ってください: {slug}")
    meta_patch(ctx, slug, {"confirmed": True})
    print(f"確定しました（採用案にしました）: {meta.get('name', '') or slug}")


def cmd_unconfirm_mock(ctx: Ctx, argv: list[str]) -> None:
    if not argv:
        die("usage: unconfirm <slug>")
    slug = argv[0]
    meta_patch(ctx, slug, {"confirmed": False})
    print(f"確定を取り消しました: {slug}")


def cmd_export(ctx: Ctx, argv: list[str]) -> None:
    if not argv:
        die("usage: export <slug> [outdir]")
    slug = argv[0]
    outdir = argv[1] if len(argv) > 1 else "./exports"
    zip_path, pattern_count, comment_count = export_pattern_core(ctx, slug, outdir)
    print(f"エクスポート完了: {zip_path}")
    print(f"  HTML    : {pattern_count} ファイル")
    print(f"  コメント: {comment_count} 件")


def cmd_rotate(ctx: Ctx, argv: list[str]) -> None:
    if not argv:
        die("usage: rotate <slug>")
    slug = argv[0]
    token, republished = rotate_token_core(ctx, slug)
    if republished:
        print("無効化済みパターンを再公開しました。")
    print()
    print(f"トークンを再発行しました: {slug}")
    print(f"  URL     : https://{ctx.domain}/p/{slug}/ （変更なし）")
    print(f"  新トークン: {token}")
    print()
    print("旧トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。新トークンを配布し直してください。")


def cmd_invalidate(ctx: Ctx, argv: list[str]) -> None:
    if not argv:
        die("usage: disable <slug> [--no-export]")
    slug = argv[0]
    no_export = len(argv) > 1 and argv[1] == "--no-export"
    invalidate_pattern_core(ctx, slug, do_export=not no_export)
    print(f"無効化しました: https://{ctx.domain}/p/{slug}/ はまもなく403を返します（エッジ反映まで数秒〜数十秒）。")
    print(f"データはS3に残っています。再エクスポートは ds.py export {slug}、再公開は ds.py rotate {slug} で可能です。")


def cmd_rename(ctx: Ctx, argv: list[str]) -> None:
    if len(argv) < 2:
        die("usage: rename <slug> <new-name>")
    slug, newname = argv[0], argv[1]
    status = meta_status(ctx, slug) or "active"
    meta_write(ctx, slug, newname, status)
    rebuild_gallery_index(ctx)
    print(f"名前を変更しました: {slug} → {newname}")


def cmd_deploy_function(ctx: Ctx, argv: list[str]) -> None:
    if not ctx.function_name:
        die("error: design-share.env に FUNCTION_NAME が必要です")
    code_path = SCRIPT_DIR.parent / "infra" / "cloudfront-function" / "edge-gate.js"
    # cf2の関数サイズ上限(10KB)に収めるため、行コメントと空行を除去してからアップロードする
    lines = []
    for line in code_path.read_text(encoding="utf-8").splitlines():
        s = line.rstrip("\n")
        st = s.lstrip()
        if st.startswith("//") or st == "":
            continue
        lines.append(s)
    minified = ("\n".join(lines) + "\n").encode("utf-8")

    etag = ctx.cf.describe_function(Name=ctx.function_name)["ETag"]
    ctx.cf.update_function(
        Name=ctx.function_name,
        IfMatch=etag,
        FunctionConfig={
            "Comment": "design-share edge-gate",
            "Runtime": "cloudfront-js-2.0",
            "KeyValueStoreAssociations": {"Quantity": 1, "Items": [{"KeyValueStoreARN": ctx.kvs_arn}]},
        },
        FunctionCode=minified,
    )
    etag2 = ctx.cf.describe_function(Name=ctx.function_name)["ETag"]
    ctx.cf.publish_function(Name=ctx.function_name, IfMatch=etag2)
    print(f"edge-gate を更新・公開しました: {ctx.function_name}")


def cmd_gallery(ctx: Ctx, argv: list[str]) -> None:
    sub = argv[0] if argv else "help"
    gallery_url = f"https://{ctx.domain}/gallery/"
    if sub == "init":
        token = new_token()
        html_path = SCRIPT_DIR.parent / "references" / "templates" / "gallery-page.html"
        if not html_path.is_file():
            die(f"error: gallery-page.html が見つかりません: {html_path}")
        ctx.s3.put_object(Bucket=ctx.bucket, Key="gallery/index.html",
                           Body=html_path.read_bytes(), ContentType="text/html; charset=utf-8")
        rebuild_gallery_index(ctx)
        kvs_put(ctx, "project:token", token)
        print()
        print("共有ギャラリーを有効化しました。")
        print(f"  URL       : {gallery_url}")
        print(f"  共通トークン: {token}")
        print()
        print("このURLと共通トークンを渡した相手は、公開中の全パターンを一覧・横断閲覧できます。")
        print("共通トークンはこの一度しか表示されません。URLとは別チャネルで共有相手に渡してください。")
        print("再発行は ds.py gallery rotate、無効化は ds.py gallery disable で行えます。")
    elif sub == "rotate":
        if not gallery_enabled(ctx):
            die("ギャラリーは未有効化です。先に ds.py gallery init を実行してください。")
        token = new_token()
        kvs_put(ctx, "project:token", token)
        print()
        print("共通トークンを再発行しました（URLは変更なし）。")
        print(f"  URL         : {gallery_url}")
        print(f"  新共通トークン: {token}")
        print()
        print("旧共通トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。")
    elif sub == "disable":
        kvs_put(ctx, "project:token", "DISABLED")
        print(f"ギャラリーを無効化しました: {gallery_url} はまもなく403を返します（エッジ反映まで数秒〜数十秒）。")
        print("各パターンの個別URL＋個別トークンでのアクセスには影響しません。再有効化は ds.py gallery init です。")
    elif sub == "url":
        print(gallery_url)
    else:
        print(__doc__)


def gurl(ctx: Ctx, gslug: str) -> str:
    return f"https://{ctx.domain}/g/{gslug}/"


def require_gslug(g: str) -> None:
    if not GSLUG_RE.match(g):
        die(f"invalid gslug: {g}")


def require_pattern(s: str) -> None:
    if not GSLUG_RE.match(s):
        die(f"invalid pattern slug: {s}")


def cmd_galleries(ctx: Ctx, argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    sub, rest = argv[0], argv[1:]
    if sub == "create":
        if not rest:
            die('usage: galleries create "<表示名>" [--key <プロジェクトキー>]')
        name = None
        project_key = ""
        pos = []
        i = 0
        while i < len(rest):
            if rest[i] == "--key":
                if i + 1 >= len(rest):
                    die("--key には値が必要です")
                project_key = rest[i + 1]
                i += 2
            else:
                pos.append(rest[i])
                i += 1
        if not pos:
            die('usage: galleries create "<表示名>" [--key <プロジェクトキー>]')
        name = pos[0]
        gslug, token, project_key = galleries_create_core(ctx, name, project_key)
        print()
        print("カテゴリ（名前付きギャラリー＝プロジェクト）を作成しました。")
        print(f"  名前          : {name}")
        print(f"  プロジェクトキー: {project_key}")
        print(f"  URL           : {gurl(ctx, gslug)}")
        print(f"  トークン        : {token}")
        print()
        print("このURLとトークンを渡した相手は、このカテゴリに入れたパターンだけを一覧・閲覧できます。")
        print(f"トークンはこの一度だけ表示。パターンの追加は ds.py galleries add {gslug} <pattern-slug> です。")
        print(f"ローカルのプロジェクトフォルダ名を「{project_key}」にすると、コンソールが自動的にこのプロジェクトと紐付けます。")
    elif sub == "list":
        keys = list_keys(ctx, "galleries/")
        if not keys:
            print("カテゴリはまだありません。")
            return
        for k in keys:
            gs = Path(k).stem
            name = gallery_meta_name(ctx, gs)
            tok = kvs_get(ctx, f"g:{gs}")
            if tok == "DISABLED":
                st = "無効"
            elif tok and tok != "None":
                st = "有効"
            else:
                st = "トークン無し"
            print(f"[{st}] {name or gs}  gslug={gs}  {gurl(ctx, gs)}")
    elif sub == "rotate":
        if not rest:
            die("usage: galleries rotate <gslug>")
        gslug = rest[0]
        require_gslug(gslug)
        token = new_token()
        kvs_put(ctx, f"g:{gslug}", token)
        print()
        print("共有トークンを再発行しました（URL不変）。")
        print(f"  URL     : {gurl(ctx, gslug)}")
        print(f"  新トークン: {token}")
        print("旧トークンはまもなく無効になります（エッジ反映まで数秒〜数十秒）。")
    elif sub == "disable":
        if not rest:
            die("usage: galleries disable <gslug>")
        gslug = rest[0]
        require_gslug(gslug)
        kvs_put(ctx, f"g:{gslug}", "DISABLED")
        print(f"カテゴリを無効化しました: {gurl(ctx, gslug)} はまもなく403になります。")
        print(f"所属パターンの個別URL・他カテゴリには影響しません。再有効化は ds.py galleries rotate {gslug} です。")
    elif sub == "delete":
        if not rest:
            die("usage: galleries delete <gslug>")
        gslug = rest[0]
        require_gslug(gslug)
        for k in list_keys(ctx, "meta/"):
            slug = Path(k).stem
            cur = pattern_galleries(ctx, slug)
            if gslug in cur:
                pattern_set_galleries(ctx, slug, [g for g in cur if g != gslug])
        try:
            ctx.kvs.delete_key(KvsARN=ctx.kvs_arn, Key=f"g:{gslug}", IfMatch=kvs_etag(ctx))
        except botocore.exceptions.ClientError:
            pass
        _s3_delete_prefix(ctx, f"g/{gslug}/")
        try:
            ctx.s3.delete_object(Bucket=ctx.bucket, Key=f"galleries/{gslug}.json")
        except botocore.exceptions.ClientError:
            pass
        rebuild_gallery_index(ctx)
        print(f"カテゴリ {gslug} を削除しました（所属パターン自体は残っています）。")
    elif sub == "export":
        if not rest:
            die("usage: galleries export <gslug> [outdir] [--all-mocks] [--mocks slug1,slug2,...]")
        gslug = rest[0]
        require_gslug(gslug)
        all_mocks = False
        explicit_mocks: list[str] | None = None
        outdir = "./exports"
        i = 1
        while i < len(rest):
            a = rest[i]
            if a == "--all-mocks":
                all_mocks = True
                i += 1
            elif a == "--mocks":
                if i + 1 >= len(rest):
                    die("--mocks には値が必要です")
                explicit_mocks = [s for s in rest[i + 1].split(",") if s]
                i += 2
            else:
                outdir = a
                i += 1
        if explicit_mocks is not None:
            mock_slugs = explicit_mocks
        elif all_mocks:
            mock_slugs = [m["slug"] for m in project_metas(ctx, gslug) if m.get("type") != "design-review"]
        else:
            mock_slugs = None  # export_project_core既定: 確定済みのみ
        zip_path, picked = export_project_core(ctx, gslug, outdir, mock_slugs=mock_slugs)
        print(f"エクスポート完了: {zip_path}")
        print(f"  DESIGN.md: {picked['design']}")
        print(f"  UIモック  : {len(picked['mocks'])}件")
    elif sub == "set":
        if not rest:
            die("usage: galleries set <pattern-slug> [gslug...]")
        slug, gslugs = rest[0], rest[1:]
        require_pattern(slug)
        for g in gslugs:
            require_gslug(g)
        pattern_set_galleries(ctx, slug, gslugs)
        print(f"更新しました: {slug} の所属カテゴリ = [ {' '.join(gslugs)} ]")
    elif sub in ("add", "remove"):
        if len(rest) < 2:
            die(f"usage: galleries {sub} <gslug> <pattern-slug>")
        gslug, slug = rest[0], rest[1]
        require_gslug(gslug)
        require_pattern(slug)
        if not gallery_meta_name(ctx, gslug):
            die(f"カテゴリが存在しません: {gslug}")
        cur = pattern_galleries(ctx, slug)
        if sub == "add":
            newlist = sorted(set(cur) | {gslug})
        else:
            newlist = [g for g in cur if g != gslug]
        pattern_set_galleries(ctx, slug, newlist)
        print(f"更新しました: {slug} の所属カテゴリ = [ {' '.join(newlist)} ]")
    else:
        print(__doc__)


def cmd_reconcile(ctx: Ctx, argv: list[str]) -> None:
    reconcile_projections(ctx)


def cmd_console(argv: list[str]) -> None:
    os.execvp("uv", ["uv", "run", "--script", str(SCRIPT_DIR / "console_server.py")])


# --- init / destroy（対話式のAWS環境ライフサイクル管理） -----------------------

def ask(prompt: str, default: str = "") -> str:
    if default:
        reply = input(f"{prompt} [{default}]: ")
        return reply or default
    return input(f"{prompt}: ")


def confirm(prompt: str) -> bool:
    reply = input(f"{prompt} [y/N]: ")
    return reply.strip().lower() == "y"


def cmd_init(argv: list[str]) -> None:
    env_target = Path(os.environ.get("DESIGN_SHARE_ENV", str(Path.cwd() / "design-share.env")))

    if env_target.is_file():
        print(f"既存の design-share.env が見つかりました: {env_target}")
        existing = load_env(env_target)
        print(f"  BUCKET={existing.get('BUCKET', '')}")
        print(f"  DISTRIBUTION_DOMAIN={existing.get('DISTRIBUTION_DOMAIN', '')}")
        if not confirm("作り直しますか？（いいえ＝このまま使う）"):
            print("既存の設定をそのまま使います。")
            return

    profile = ask("AWSプロファイル（空欄=デフォルトプロファイル）", os.environ.get("AWS_PROFILE", ""))
    try:
        base_session = boto3.Session(profile_name=profile or None)
        caller = base_session.client("sts").get_caller_identity()
    except Exception as e:
        die(f"error: AWS認証情報が見つかりません。先に 'aws sso login' 等でログインしてください。\n{e}")
    account_id = caller["Account"]
    print(f"認証OK: Account={account_id}")

    default_region = base_session.region_name or ""
    region = ask("リージョン", default_region or "ap-northeast-1")
    session = boto3.Session(profile_name=profile or None, region_name=region)
    cfn = session.client("cloudformation")

    stack_name = ask("スタック名", "design-share")

    existing_status = None
    try:
        existing_status = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]["StackStatus"]
    except botocore.exceptions.ClientError:
        existing_status = None

    if existing_status:
        print(f"スタック '{stack_name}' は既に存在します（状態: {existing_status}）。新規作成はスキップし、Outputsを取得します。")
    else:
        print(f"スタック '{stack_name}' は存在しません。新規作成します。")
        default_bucket = f"design-share-{account_id}-{region.replace('-', '')}"
        bucket_name = ask("S3バケット名（グローバルに一意である必要があります）", default_bucket)
        price_class = ask("CloudFront価格クラス（PriceClass_100 / PriceClass_200 / PriceClass_All）", "PriceClass_200")

        print()
        print("以下の内容で実際にAWSリソースを作成します（S3バケット・CloudFront Distribution等、課金が発生します）:")
        print(f"  スタック名   : {stack_name}")
        print(f"  リージョン   : {region}")
        print(f"  バケット名   : {bucket_name}")
        print(f"  価格クラス   : {price_class}")
        if not confirm("作成してよいですか？"):
            die("中止しました。")

        template_body = (SCRIPT_DIR.parent / "infra" / "cloudformation.yaml").read_text(encoding="utf-8")
        cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {"ParameterKey": "BucketName", "ParameterValue": bucket_name},
                {"ParameterKey": "PriceClass", "ParameterValue": price_class},
            ],
            Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        )
        print("スタック作成中（完了まで待機します）...")
        cfn.get_waiter("stack_create_complete").wait(StackName=stack_name)
        print("スタック作成完了。")

    outputs = {o["OutputKey"]: o["OutputValue"]
               for o in cfn.describe_stacks(StackName=stack_name)["Stacks"][0].get("Outputs", [])}

    lines = [
        f"BUCKET={outputs['BucketNameOut']}",
        f"DISTRIBUTION_DOMAIN={outputs['DistributionDomain']}",
        f"KVS_ARN={outputs['TokenStoreArn']}",
        f"FUNCTION_NAME={outputs['EdgeGateFunctionName']}",
    ]
    env_target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"design-share.env を書き出しました: {env_target}")

    print("edge-gate関数を反映・公開します...")
    os.environ["DESIGN_SHARE_ENV"] = str(env_target)
    if profile:
        os.environ["AWS_PROFILE"] = profile
    os.environ["AWS_DEFAULT_REGION"] = region
    cmd_deploy_function(Ctx(), [])

    print()
    print("初期化完了。以降は同じディレクトリ（または DESIGN_SHARE_ENV 指定）で ds.py の各コマンドが使えます。")


def _s3_delete_all(s3_client, bucket: str) -> None:
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        for i in range(0, len(objs), 1000):
            batch = objs[i:i + 1000]
            if batch:
                s3_client.delete_objects(Bucket=bucket, Delete={"Objects": batch})


def cmd_destroy(argv: list[str]) -> None:
    env_candidate = Path(os.environ.get("DESIGN_SHARE_ENV", str(Path.cwd() / "design-share.env")))
    if env_candidate.is_file():
        print(f"現在の design-share.env: {env_candidate}")

    profile = ask("AWSプロファイル（空欄=デフォルトプロファイル）", os.environ.get("AWS_PROFILE", ""))
    try:
        base_session = boto3.Session(profile_name=profile or None)
        caller = base_session.client("sts").get_caller_identity()
    except Exception:
        die("error: AWS認証情報が見つかりません。先に 'aws sso login' 等でログインしてください。")
    account_id = caller["Account"]
    print(f"認証OK: Account={account_id}")

    default_region = base_session.region_name or ""
    region = ask("リージョン", default_region or "ap-northeast-1")
    session = boto3.Session(profile_name=profile or None, region_name=region)
    cfn = session.client("cloudformation")
    s3 = session.client("s3")

    stack_name = ask("削除対象のスタック名", "design-share")

    try:
        stack = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]
    except botocore.exceptions.ClientError:
        die(f"error: スタック '{stack_name}'（リージョン {region}）が見つかりません。")
    status = stack["StackStatus"]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
    bucket = outputs.get("BucketNameOut", "")
    domain = outputs.get("DistributionDomain", "")

    obj_count = 0
    if bucket:
        try:
            obj_count = len(s3.list_objects_v2(Bucket=bucket).get("Contents", []))
        except botocore.exceptions.ClientError:
            obj_count = 0

    print()
    print("以下を削除します（元に戻せません）:")
    print(f"  スタック名   : {stack_name}（状態: {status}）")
    print(f"  リージョン   : {region}")
    print(f"  バケット     : {bucket}（オブジェクト数: {obj_count}）")
    print(f"  配信ドメイン : {domain}")
    print()
    confirm_name = input(f"本当に削除する場合は、スタック名 '{stack_name}' を正確にタイプしてください: ")
    if confirm_name != stack_name:
        die("入力が一致しないため中止しました。")

    if obj_count and bucket:
        print(f"バケットを空にしています（{obj_count} 件）...")
        _s3_delete_all(s3, bucket)

    print("スタックを削除しています（CloudFront Distributionの無効化待ちで15〜20分程度かかることがあります）...")
    cfn.delete_stack(StackName=stack_name)
    cfn.get_waiter("stack_delete_complete").wait(StackName=stack_name)

    print(f"削除完了: {stack_name}")
    if env_candidate.is_file():
        env_bucket = load_env(env_candidate).get("BUCKET", "")
        if env_bucket == bucket:
            print(f"注意: 削除したスタックは {env_candidate} が指す環境と同じです。このファイルはもう無効です。")


# --- smoke test ---------------------------------------------------------------

def poll(n: int, sleep_s: float, desc: str, fn) -> bool:
    for _ in range(n):
        if fn():
            return True
        time.sleep(sleep_s)
    print(f"    （{desc}: {n}回リトライしても条件を満たしませんでした）")
    return False


def streak_ok(n: int, sleep_s: float, need: int, desc: str, fn) -> bool:
    streak = 0
    for _ in range(n):
        streak = streak + 1 if fn() else 0
        if streak >= need:
            return True
        time.sleep(sleep_s)
    print(f"    （{desc}: 連続{need}回に届かず）")
    return False


def cmd_smoke(ctx: Ctx, argv: list[str]) -> int:
    passed = 0
    failed = 0

    def ok(msg: str) -> None:
        nonlocal passed
        print(f"  \033[32mPASS\033[0m {msg}")
        passed += 1

    def ng(msg: str) -> None:
        nonlocal failed
        print(f"  \033[31mFAIL\033[0m {msg}")
        failed += 1

    def info(msg: str) -> None:
        print(f"\n\033[1m{msg}\033[0m")

    base = f"https://{ctx.domain}"
    marker = "smoke-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    state = {"slug": None}

    def cleanup() -> None:
        # テストパターンは無効化して痕跡を残さない（データはS3に残る＝安全側）
        if state["slug"]:
            info(f"Cleanup: テストパターン {state['slug']} を無効化します（データはS3に残ります）")
            try:
                invalidate_pattern_core(ctx, state["slug"], do_export=False)
            except Exception:
                pass

    def _do_request(url: str, headers: dict | None = None, method: str = "GET",
                     data: bytes | None = None, jar: http.cookiejar.CookieJar | None = None):
        req = urllib.request.Request(url, headers=headers or {}, method=method, data=data)
        try:
            if jar is not None:
                opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
                with opener.open(req, timeout=15) as resp:
                    return resp.status, resp.read(), resp.headers
            else:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.status, resp.read(), resp.headers
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            return e.code, body, e.headers
        except Exception:
            return 0, b"", None

    def get_code(url: str, headers: dict | None = None, jar=None) -> int:
        return _do_request(url, headers=headers, jar=jar)[0]

    def get_body(url: str, headers: dict | None = None, jar=None) -> str:
        _, body, _ = _do_request(url, headers=headers, jar=jar)
        return body.decode("utf-8", "replace")

    def put_code(url: str, body_bytes: bytes, jar, content_type: str = "application/json") -> int:
        sha = hashlib.sha256(body_bytes).hexdigest()
        headers = {"content-type": content_type, "x-amz-content-sha256": sha}
        return _do_request(url, headers=headers, method="PUT", data=body_bytes, jar=jar)[0]

    try:
        info("0. 前提チェック")
        ok("boto3/urllibで完結（aws CLI・curl等の外部コマンドに依存しない）")

        info("1. 使い捨てテストパターンをデプロイ")
        html = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>smoke</title></head>'
                f'<body><main>smoke test page {marker}</main></body></html>')
        fd, tmp_html = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            slug, token, _ = deploy_pattern_core(ctx, tmp_html, f"smoke-test {marker}")
            state["slug"] = slug
            ok(f"deploy 成功 slug={slug}")
        except Exception as e:
            ng(f"deploy 失敗（URL/トークンを取得できず）: {e}")
            return 1
        finally:
            os.unlink(tmp_html)

        info("2. デプロイのエッジ伝播を待つ（KVS結果整合）")

        def verify_code() -> int:
            return get_code(f"{base}/p/{slug}/verify", headers={"x-share-token": token})

        def wait_converged() -> bool:
            streak = 0
            for _ in range(50):
                streak = streak + 1 if verify_code() == 204 else 0
                if streak >= 4:
                    return True
                time.sleep(3)
            return False

        if wait_converged():
            ok("トークンがエッジへ収束伝播（verify=204が連続）")
        else:
            ng(f"伝播待ちタイムアウト（verify={verify_code()}）※edge-gate未反映(503)の可能性")

        info("3. 負の認証（トークン無し・誤トークン）")
        notoken = get_code(f"{base}/p/{slug}/")
        ok(f"トークン無し → 拒否({notoken})") if notoken in (401, 403) else ng(f"トークン無しでページが通る（{notoken}）")
        wrong = get_code(f"{base}/p/{slug}/verify", headers={"x-share-token": f"WRONG-{marker}"})
        ok("誤トークン → 401") if wrong == 401 else ng(f"誤トークンで 401 以外（実際: {wrong}）")

        info("4. Cookie発行とページ本体")
        jar = http.cookiejar.CookieJar()

        def verify_get() -> int:
            return get_code(f"{base}/p/{slug}/verify", headers={"x-share-token": token}, jar=jar)

        right = verify_get()
        for _ in range(8):
            if right == 204:
                break
            time.sleep(5)
            right = verify_get()
        ok("正トークン → 204") if right == 204 else ng(f"正トークンで 204 以外（実際: {right}）")
        has_cookie = any(c.name == f"share_{slug}" for c in jar)
        ok(f"share_{slug} Cookie が発行された") if has_cookie else ng("Cookie が発行されない")
        _, _, hdrs = _do_request(f"{base}/p/{slug}/verify", headers={"x-share-token": token})
        setcookie = "\n".join(hdrs.get_all("Set-Cookie") or []) if hdrs else ""
        if all(x in setcookie.lower() for x in ("secure", "httponly", "samesite=strict")):
            ok("Cookie属性 Secure/HttpOnly/SameSite=Strict")
        else:
            ng(f"Cookie属性が不足: {setcookie}")

        def page_ok() -> bool:
            return marker in get_body(f"{base}/p/{slug}/", jar=jar)

        if poll(6, 5, "本体取得リトライ", page_ok):
            ok("Cookie付き → ページ本体200（マーカー一致）")
        else:
            ng("Cookie付きでもページ本体を取得できない")

        info("5. コメント投稿（OAC署名PUT）")
        body_json = json.dumps({"author": "smoke", "body": marker, "postedAt": "2026-01-01T00:00:00Z"}).encode("utf-8")
        key = f"comments/{slug}/{int(time.time())}-smoke.json"

        def put_ok() -> bool:
            return 200 <= put_code(f"{base}/{key}", body_json, jar) < 300

        if poll(6, 5, "PUTリトライ(伝播裾)", put_ok):
            ok("コメントPUT → 2xx（OAC署名PUT成立）")
        else:
            ng("コメントPUT失敗 ★これが失敗ならコメント投稿だけFunction URL等へ逃がす代替が必要")

        info("5b. コメントPUT拒否経路（負テスト）")
        dummy = b'{"author":"x","body":"x","postedAt":"2026-01-01T00:00:00Z"}'
        c1 = put_code(f"{base}/comments/{slug}/evil.html", dummy, jar)
        ok("非.jsonキーPUT → 403") if c1 == 403 else ng(f"非.jsonキーPUTが403以外（{c1}）")
        c2 = put_code(f"{base}/comments/{slug}/{int(time.time() * 1000)}-x.json", dummy, jar, content_type="text/html")
        ok("content-type=text/html → 403") if c2 == 403 else ng(f"不正content-typeが403以外（{c2}）")
        c3 = get_code(f"{base}/p/{slug}/", jar=jar) if False else _do_request(f"{base}/p/{slug}/", method="DELETE", jar=jar)[0]
        ok("DELETE → 403") if c3 == 403 else ng(f"DELETEが403以外（{c3}）")
        big = ('{"author":"x","body":"' + "a" * 20000 + '"}').encode("utf-8")
        c4 = put_code(f"{base}/comments/{slug}/{int(time.time() * 1000)}-big.json", big, jar)
        ok("16KB超PUT → 403") if c4 == 403 else ng(f"巨大PUTが403以外（{c4}）")

        info("6. コメント一覧と本文取得")

        def list_has_key() -> bool:
            return f"<Key>comments/{slug}/" in get_body(f"{base}/comments-list/{slug}", jar=jar)

        if poll(10, 3, "一覧反映待ち", list_has_key):
            ok("comments-list に投稿キーが出る（ListObjectsV2書き換え成立）")
        else:
            ng("comments-list に投稿が現れない")
        got = get_body(f"{base}/{key}", jar=jar)
        ok("コメント本文を取得できる") if marker in got else ng("コメント本文を取得できない")

        info("6b. カテゴリのスコープ制御（最重要）")
        fd2, tmp2 = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd2, "w", encoding="utf-8") as f2:
            f2.write(f'<!doctype html><title>s2</title><main>NONMEMBER-{marker}</main>')
        slug2 = catg = cattok = None
        try:
            slug2, _tok2, _ = deploy_pattern_core(ctx, tmp2, f"smoke-nonmember {marker}")
        except Exception:
            pass
        finally:
            os.unlink(tmp2)
        try:
            catg, cattok, _ = galleries_create_core(ctx, f"smoke-cat {marker}")
            pattern_set_galleries(ctx, slug, list(set(pattern_galleries(ctx, slug)) | {catg}))
        except Exception:
            pass
        if slug2 and catg and cattok:
            def cat_ok() -> bool:
                return get_code(f"{base}/g/{catg}/verify", headers={"x-share-token": cattok}) == 204

            streak_ok(30, 3, 4, "カテゴリトークン収束", cat_ok)
            cjar = http.cookiejar.CookieJar()
            _do_request(f"{base}/g/{catg}/verify", headers={"x-share-token": cattok}, jar=cjar)

            def memb_ok() -> bool:
                return get_code(f"{base}/p/{slug}/", jar=cjar) == 200

            if streak_ok(30, 3, 3, "所属案アクセス収束", memb_ok):
                ok("所属案 → カテゴリCookieで200（横断成立）")
            else:
                ng("所属案がカテゴリCookieで開けない")
            nm = get_code(f"{base}/p/{slug2}/", jar=cjar)
            ok("★非所属案 → 401（スコープ遮断）") if nm == 401 else ng(f"★非所属案がカテゴリCookieで開ける（{nm}）＝スコープ漏れ")
            try:
                cur = pattern_galleries(ctx, slug)
                if catg in cur:
                    pattern_set_galleries(ctx, slug, [g for g in cur if g != catg])
                ctx.kvs.delete_key(KvsARN=ctx.kvs_arn, Key=f"g:{catg}", IfMatch=kvs_etag(ctx))
                _s3_delete_prefix(ctx, f"g/{catg}/")
                ctx.s3.delete_object(Bucket=ctx.bucket, Key=f"galleries/{catg}.json")
                rebuild_gallery_index(ctx)
            except Exception:
                pass
            try:
                invalidate_pattern_core(ctx, slug2, do_export=False)
            except Exception:
                pass
        else:
            ng(f"スコープテストの準備に失敗（slug2={slug2} cat={catg}）")

        info("7. トークンローテーション")
        new_tok, _ = rotate_token_core(ctx, slug)
        ok("新トークン発行（旧と異なる）") if (new_tok and new_tok != token) else ng("新トークンを取得できない")

        def old_dead() -> bool:
            return get_code(f"{base}/p/{slug}/", jar=jar) == 401

        if streak_ok(30, 3, 4, "旧トークン失効の収束", old_dead):
            ok("旧トークンCookie → 401（収束確認）")
        else:
            ng("旧トークンCookieがまだ通る（収束せず）")

        info("8. 無効化とデータ保全")
        invalidate_pattern_core(ctx, slug, do_export=False)

        def disabled() -> bool:
            return get_code(f"{base}/p/{slug}/verify", headers={"x-share-token": new_tok}) == 403

        if streak_ok(30, 3, 4, "無効化の収束", disabled):
            ok("無効化後は正トークンでも403（収束確認）")
        else:
            ng("無効化後もアクセスできる（収束せず）")
        with tempfile.TemporaryDirectory() as export_dir:
            try:
                zip_path, _, _ = export_pattern_core(ctx, slug, export_dir)
                ok("無効化後もエクスポート可能（データは削除されていない）") if zip_path.is_file() \
                    else ng("無効化後にエクスポートできない（データ保全の前提が崩れている）")
            except Exception as e:
                ng(f"無効化後にエクスポートできない: {e}")
        state["slug"] = None  # 後始末済み。二重無効化を避ける

    except Exception as e:
        ng(f"予期しない例外で中断: {e}")
    finally:
        cleanup()

    info(f"自動チェック結果: PASS={passed} FAIL={failed}")
    print("""
--- 以下は自動化できないため、ブラウザで手動確認してください ---
[ ] XSS: コメント本文に <img src=x onerror=alert(1)> 等を投稿し、
        画面上でタグがそのまま文字列として表示される（実行されない）こと
[ ] Cookie属性: DevTools の Application > Cookies で share_{slug} が
        Secure / HttpOnly / SameSite=Strict になっていること
[ ] UI: パターンページのレイアウト・コメント欄・投稿フォームが
        Design.md のトークン通りに崩れず表示されること
[ ] 横断遷移: 別パターンのURLへ遷移でき、それぞれ独立にゲートされること
""")
    return 0 if failed == 0 else 1


# --- エントリポイント ----------------------------------------------------------

def main() -> None:
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "help"
    rest = argv[1:]

    if cmd in ("help", "-h", "--help"):
        print(__doc__)
        return
    if cmd == "init":
        cmd_init(rest)
        return
    if cmd == "destroy":
        cmd_destroy(rest)
        return
    if cmd == "console":
        cmd_console(rest)
        return

    ctx = Ctx()
    if cmd == "list":
        cmd_list(ctx, rest)
    elif cmd == "deploy":
        cmd_deploy(ctx, rest)
    elif cmd == "redeploy":
        cmd_redeploy(ctx, rest)
    elif cmd == "confirm-design":
        cmd_confirm_design(ctx, rest)
    elif cmd == "confirm":
        cmd_confirm_mock(ctx, rest)
    elif cmd == "unconfirm":
        cmd_unconfirm_mock(ctx, rest)
    elif cmd == "export":
        cmd_export(ctx, rest)
    elif cmd == "rotate":
        cmd_rotate(ctx, rest)
    elif cmd == "disable":
        cmd_invalidate(ctx, rest)
    elif cmd == "rename":
        cmd_rename(ctx, rest)
    elif cmd == "update-function":
        cmd_deploy_function(ctx, rest)
    elif cmd == "gallery":
        cmd_gallery(ctx, rest)
    elif cmd == "galleries":
        cmd_galleries(ctx, rest)
    elif cmd == "reconcile":
        cmd_reconcile(ctx, rest)
    elif cmd == "smoke":
        sys.exit(cmd_smoke(ctx, rest))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

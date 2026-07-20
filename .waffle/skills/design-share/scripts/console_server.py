#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3", "awscrt"]
# ///
"""console_server.py — 作成者向け横断管理コンソール（localhostのみ・本番非公開）。

合意事項（ブレスト論点6・7）:
  - 本番AWS環境にはデプロイしない。Claude Code上でこのスクリプトを起動し、
    起動時に表示されるURL（乱数トークン付き）をブラウザで開く
  - 認証は開発者が既に持つAWS認証情報（aws cli）をそのまま使う
  - 全セッション・全パターンを横断して一覧し、操作は行ごとの「⋯」メニューから行う
    （エクスポート/名前変更/トークン再発行/無効化・再公開）。共有ギャラリーの
    有効化/共通トークン再発行/無効化も同画面から行える

セキュリティ（advisor批評の反映）:
  - Hostヘッダー検証（DNSリバインディング対策）
  - 変更系APIは起動時乱数トークンを X-Console-Token ヘッダーで要求
    （カスタムヘッダー必須 = ブラウザのプリフライトが強制され、外部サイトからのCSRFを遮断）

依存関係について:
  読み取り経路（一覧取得）は boto3 を使う。PEP 723のインラインメタデータ（先頭の # /// script）で
  宣言しているため、`uv run scripts/console_server.py` で実行すればプロジェクト全体のvenvを汚さず
  自動的に隔離環境へ導入される（design-shareの自己完結性を保つ）。書き込み系操作（deploy/disable等）
  は run_script() 経由で ds.py（同じくuv run --script + boto3）へ委譲する。

使い方: uv run scripts/console_server.py  （design-share.env のあるディレクトリで実行、
        または DESIGN_SHARE_ENV に絶対パスを設定。uvが無い環境では
        `pip install boto3` 後に python3 console_server.py でも動く）
"""
import http.server
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import boto3

HOST, PORT = "127.0.0.1", 8787
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
CONSOLE_TOKEN = secrets.token_urlsafe(16)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def resolve_env_path() -> str:
    env_path = os.path.abspath(os.environ.get("DESIGN_SHARE_ENV", "./design-share.env"))
    if not os.path.exists(env_path):
        sys.exit(f"error: {env_path} がありません。CloudFormation Outputsから作成してください。")
    return env_path


ENV_PATH = resolve_env_path()


def load_env() -> dict:
    conf = {}
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k.startswith("export "):  # `export AWS_PROFILE=dev` 形式に対応
                    k = k[len("export "):].strip()
                conf[k] = v
    return conf


CONF = load_env()
# env内のAWS認証情報（SSO名前付きプロファイル等）をこのプロセスのaws呼び出しにも適用する。
# これがないと、シェルにAWS_PROFILEを export せずに起動した場合に一覧が空になる。
for _k in ("AWS_PROFILE", "AWS_REGION", "AWS_DEFAULT_REGION"):
    if CONF.get(_k):
        os.environ.setdefault(_k, CONF[_k])

GALLERY_URL = f"https://{CONF.get('DISTRIBUTION_DOMAIN', '')}/gallery/"

# 読み取り経路（一覧取得）はこのプロセス内のboto3で直接行う（サブプロセス起動コストを避けるため）。
# 書き込み系はrun_script()経由でds.py（uv run --script）へ委譲する。
_BOTO_SESSION = boto3.Session(
    profile_name=CONF.get("AWS_PROFILE") or None,
    region_name=CONF.get("AWS_REGION") or CONF.get("AWS_DEFAULT_REGION") or None,
)
_S3 = _BOTO_SESSION.client("s3")
_KVS = _BOTO_SESSION.client("cloudfront-keyvaluestore")


def aws(*args: str) -> str:
    return subprocess.run(["aws", *args], check=True, capture_output=True, text=True).stdout


def kvs_get(key: str) -> str:
    # ResourceNotFoundException（キー未設定）は「空」として正常に扱うが、それ以外の例外
    # （依存不足・権限エラー等）は空文字へ静かに丸めず必ずログへ残す。
    # 値の握りつぶしが「未設定」と「取得失敗」を区別不能にしていたため、これで検知できるようにする
    try:
        return _KVS.get_key(KvsARN=CONF["KVS_ARN"], Key=key).get("Value", "")
    except _KVS.exceptions.ResourceNotFoundException:
        return ""
    except Exception as e:
        print(f"kvs_get({key!r}) failed: {e}", file=sys.stderr)
        return ""


def run_script(cmd: str, *args: str) -> tuple[bool, str]:
    # 書き込み系操作はds.py（uv run --script経由）へ委譲する。DESIGN_SHARE_ENVを
    # 絶対パスで渡すため、cwdに依存しない
    env = {**os.environ, "DESIGN_SHARE_ENV": ENV_PATH}
    proc = subprocess.run(
        ["uv", "run", "--script", os.path.join(SCRIPT_DIR, "ds.py"), cmd, *args],
        capture_output=True, text=True, cwd=os.getcwd(), env=env,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def list_patterns() -> list[dict]:
    # 一覧取得(list-objects)の失敗は認証/権限エラー＝「0件」と誤認させず伝播させる。
    # （空バケットは Contents=null で成功し keys=[] になる。ここでの例外は本物の失敗）
    resp = _S3.list_objects_v2(Bucket=CONF["BUCKET"], Prefix="meta/")
    keys = [o["Key"] for o in resp.get("Contents", [])]

    # 一覧表示にはKVSのトークン値は不要（statusはmeta.json側に既に持っている）。
    # KVSのSigV4A署名は1回あたり約1.3秒かかり並列化しても縮まらないため、一覧では叩かない。
    # トークンの実値は共有メニューを開いたときに /api/token でオンデマンド取得する
    def fetch_one(key: str) -> dict | None:
        try:
            body = _S3.get_object(Bucket=CONF["BUCKET"], Key=key)["Body"].read()
            return json.loads(body)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=min(32, max(4, len(keys)))) as ex:
        patterns = [p for p in ex.map(fetch_one, keys) if p is not None]
    return sorted(patterns, key=lambda p: p.get("updatedAt", ""), reverse=True)


def gallery_status() -> str:
    v = kvs_get("project:token")
    if not v or v == "None":
        return "unset"
    return "disabled" if v == "DISABLED" else "enabled"


def galleries_list() -> list[dict]:
    # 一覧取得の失敗は伝播させる（0件と誤認しない）
    resp = _S3.list_objects_v2(Bucket=CONF["BUCKET"], Prefix="galleries/")
    keys = [o["Key"] for o in resp.get("Contents", [])]

    def fetch_cat(key: str) -> dict | None:
        gs = key.split("/")[-1].rsplit(".json", 1)[0]
        try:
            body = _S3.get_object(Bucket=CONF["BUCKET"], Key=key)["Body"].read()
            meta = json.loads(body)
        except Exception:
            return None
        v = kvs_get(f"g:{gs}")
        status = "disabled" if v == "DISABLED" else ("enabled" if v and v != "None" else "unset")
        # トークンの実値は一覧に含めない。共有メニューを開いたときに /api/token でオンデマンド取得する
        return {"gslug": gs, "name": meta.get("name", ""), "status": status,
                "url": f"https://{CONF.get('DISTRIBUTION_DOMAIN', '')}/g/{gs}/"}

    with ThreadPoolExecutor(max_workers=8) as ex:
        cats = [c for c in ex.map(fetch_cat, keys) if c is not None]
    return sorted(cats, key=lambda c: c["name"])


_PRICING_CACHE = None


def pricing() -> dict:
    # AWS Price List API から現行オンデマンド単価を取得（東京リージョン）。
    # Price List API が安定して返す項目（S3・CloudFront Functions）はライブ取得し、
    # 露出が不安定な項目（CloudFront 標準リクエスト/転送）は公示レートにフォールバックする。
    # 各単価に出所(api/published)を付す。プロセス内で1度だけ取得しキャッシュ。
    global _PRICING_CACHE
    if _PRICING_CACHE is not None:
        return _PRICING_CACHE

    def unit(service_code, filters):
        args = ["pricing", "get-products", "--region", "us-east-1",
                "--service-code", service_code, "--max-items", "6"]
        for f in filters:
            args += ["--filters", f]
        try:
            best = None
            for pjson in json.loads(aws(*args)).get("PriceList", []):
                o = json.loads(pjson)
                for t in o.get("terms", {}).get("OnDemand", {}).values():
                    for d in t.get("priceDimensions", {}).values():
                        v = float(d.get("pricePerUnit", {}).get("USD", "0") or 0)
                        if v > 0 and (best is None or v > best):  # $0(無料/beginRange0)は除き有料ティアを採る
                            best = v
            return best
        except (subprocess.CalledProcessError, ValueError, KeyError):
            return None

    def fb(v, published):
        return {"usd": v, "src": "api"} if v is not None else {"usd": published, "src": "published"}

    tokyo = "Type=TERM_MATCH,Field=location,Value=Asia Pacific (Tokyo)"
    p = {
        "s3_put_list": fb(unit("AmazonS3", [tokyo, "Type=TERM_MATCH,Field=group,Value=S3-API-Tier1"]), 0.0055 / 1000),
        "s3_get": fb(unit("AmazonS3", [tokyo, "Type=TERM_MATCH,Field=group,Value=S3-API-Tier2"]), 0.0042 / 10000),
        "s3_storage_gb": fb(unit("AmazonS3", [tokyo, "Type=TERM_MATCH,Field=storageClass,Value=General Purpose",
                                              "Type=TERM_MATCH,Field=volumeType,Value=Standard"]), 0.025),
        "cf_functions": fb(unit("AmazonCloudFront", ["Type=TERM_MATCH,Field=usagetype,Value=Executions-CloudFrontFunctions"]), 0.10 / 1e6),
        "cf_request": fb(None, 0.0120 / 1e4),   # Price List APIで安定取得できないため公示レート
        "cf_transfer_gb": fb(None, 0.114),
        "free": {"cf_req": 10e6, "cf_func": 2e6, "xfer_gb": 1000},
    }
    _PRICING_CACHE = p
    return p


def state() -> dict:
    # patternsは高速（KVS不要）。galleries_list/gallery_statusはそれぞれ内部でKVSのSigV4A署名
    # （1回約1.3秒）を伴うため、この2つを互いに直列に呼ぶと待ち時間が積み上がる。並列に走らせる
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_patterns = ex.submit(list_patterns)
        f_cats = ex.submit(galleries_list)
        f_gstatus = ex.submit(gallery_status)
        patterns, cats, gstatus = f_patterns.result(), f_cats.result(), f_gstatus.result()
    for c in cats:
        c["count"] = sum(1 for p in patterns if c["gslug"] in (p.get("galleries") or []))
    # トークンの実値は一覧に含めない。共有メニューを開いたときに /api/token でオンデマンド取得する
    return {"patterns": patterns,
            "gallery": {"status": gstatus, "url": GALLERY_URL},
            "categories": cats}


def fetch_token_for(kind: str, ident: str) -> str:
    if kind == "pattern":
        v = kvs_get("token:" + ident)
    elif kind == "gallery":
        v = kvs_get(f"g:{ident}")
    elif kind == "global":
        v = kvs_get("project:token")
    else:
        return ""
    return "" if v in ("", "None", "DISABLED") else v


PAGE = r"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>design-share console</title>
<style>
:root{--ground:#F1F4F6;--surface:#FFFFFF;--surface-2:#F7F9FA;--ink:#1C2733;--muted:#5A6B7A;--faint:#8494A1;
--line:#E1E5EA;--accent:#2F6F76;--accent-ink:#FFF;--pos-bg:#E2F0E8;--pos-fg:#1E7A50;--crit-bg:#F6E5E3;--crit-fg:#B23A30;
--shadow:0 1px 2px rgba(28,39,51,.06),0 8px 24px rgba(28,39,51,.06);--radius:10px;
--mono:ui-monospace,"SF Mono","IBM Plex Mono",Menlo,monospace;--sans:system-ui,-apple-system,"Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif}
@media(prefers-color-scheme:dark){:root{--ground:#10161C;--surface:#19222B;--surface-2:#1E2831;--ink:#E7EDF1;--muted:#9DAAB5;
--faint:#6E7E8B;--line:#2A353F;--accent:#52A2A9;--accent-ink:#06171A;--pos-bg:#16332A;--pos-fg:#67C79A;--crit-bg:#3A211F;--crit-fg:#E58B80;
--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35)}}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);line-height:1.5;padding:clamp(1rem,4vw,2.4rem) 1rem 4rem}
.wrap{max-width:940px;margin:0 auto}
header.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem 1rem;margin-bottom:.3rem}
header.top h1{font-size:1.3rem;font-weight:650;margin:0;letter-spacing:-.01em}
.env{font-family:var(--mono);font-size:.72rem;color:var(--muted);background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:.15rem .6rem}
.sub{color:var(--muted);font-size:.85rem;margin:.1rem 0 1.3rem}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin-bottom:1.2rem}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:.8rem 1rem;box-shadow:var(--shadow)}
.stat .n{font-size:1.6rem;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat .k{font-family:var(--mono);font-size:.66rem;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);margin-top:.1rem}
.stat.pos .n{color:var(--pos-fg)}.stat.crit .n{color:var(--crit-fg)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:1.2rem}
.panel .ph{display:flex;align-items:center;gap:.6rem;padding:.7rem 1.1rem;border-bottom:1px solid var(--line);background:var(--surface-2);border-radius:var(--radius) var(--radius) 0 0}
.panel .ph h2{font-size:.78rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);margin:0;flex:1}
.gwrap{display:flex;align-items:center;gap:.7rem;flex-wrap:wrap;padding:.9rem 1.1rem}
.gwrap .gurl{font-family:var(--mono);font-size:.78rem;color:var(--accent);word-break:break-all;flex:1;min-width:12rem}
.gwrap .goff{font-size:.82rem;color:var(--muted);flex:1;min-width:12rem}
table{width:100%;border-collapse:collapse}
thead th{text-align:left;font-family:var(--mono);font-size:.66rem;letter-spacing:.03em;text-transform:uppercase;color:var(--faint);font-weight:600;padding:.7rem 1.1rem;border-bottom:1px solid var(--line)}
tbody td{padding:.8rem 1.1rem;border-bottom:1px solid var(--line);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
.name{font-weight:600}.slug{font-family:var(--mono);font-size:.78rem;color:var(--muted)}
.date{font-family:var(--mono);font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-flex;align-items:center;gap:.35rem;font-size:.72rem;font-weight:600;padding:.18rem .6rem;border-radius:999px;white-space:nowrap}
.pill::before{content:"";width:.45rem;height:.45rem;border-radius:50%;background:currentColor}
.pill.active{background:var(--pos-bg);color:var(--pos-fg)}.pill.disabled{background:var(--crit-bg);color:var(--crit-fg)}
.pill.unset{background:var(--surface-2);color:var(--faint)}
td.c-actions{text-align:right}
.menu-wrap{position:relative;display:inline-block}
button.kebab{font:inherit;cursor:pointer;width:2rem;height:2rem;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--muted);transition:background .12s,border-color .12s,color .12s}
button.kebab:hover,button.kebab[aria-expanded=true]{background:var(--surface-2);border-color:var(--accent);color:var(--ink)}
button.kebab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.kebab svg{width:1.1rem;height:1.1rem;display:block}
.menu{position:absolute;right:0;top:calc(100% + .35rem);z-index:40;min-width:13rem;background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:0 6px 16px rgba(28,39,51,.14),0 12px 40px rgba(28,39,51,.18);padding:.35rem;display:none;text-align:left}
.menu.open{display:block;animation:pop .1s ease-out}
@keyframes pop{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.menu button.item{font:inherit;font-size:.82rem;width:100%;text-align:left;cursor:pointer;display:flex;align-items:center;gap:.6rem;padding:.5rem .6rem;border:none;border-radius:7px;background:transparent;color:var(--ink);transition:background .1s}
.menu button.item .ic{width:1.05rem;text-align:center;color:var(--muted);flex:none}
.menu button.item:hover,.menu button.item:focus-visible{background:var(--surface-2);outline:none}
.menu button.item.danger{color:var(--crit-fg)}.menu button.item.danger .ic{color:var(--crit-fg)}
.menu button.item.danger:hover,.menu button.item.danger:focus-visible{background:var(--crit-bg)}
.menu button.item.good{color:var(--pos-fg)}.menu button.item.good .ic{color:var(--pos-fg)}
.menu .sep{height:1px;background:var(--line);margin:.3rem .2rem}
button.mini{font:inherit;font-size:.78rem;font-weight:600;cursor:pointer;padding:.32rem .8rem;border-radius:7px;border:1px solid var(--line);background:var(--surface);color:var(--ink)}
button.mini:hover{background:var(--surface-2);border-color:var(--accent)}
button.mini.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
#g-actions{display:inline-flex;align-items:center;gap:.55rem}
.catrow{display:flex;align-items:center;gap:.6rem;padding:.7rem 1.1rem;border-bottom:1px solid var(--line);cursor:pointer}
.catrow:last-child{border-bottom:none}
.catrow:hover{background:var(--surface-2)}
.catrow.sel{background:color-mix(in srgb,var(--accent) 13%,var(--surface))}
.catrow .cname{font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;gap:.4rem}
.catrow .cname .caret{color:var(--faint);flex:none}
.catrow.sel .cname .caret{color:var(--accent)}
.catrow .cmeta{font-family:var(--mono);font-size:.72rem;color:var(--faint);flex:none}
.catrow .cactions{flex:none}
.cempty{padding:.9rem 1.1rem;color:var(--muted);font-size:.85rem}
.pfilter{font-family:var(--mono);font-size:.68rem;color:var(--accent);font-weight:600}
.pfilter .clear{cursor:pointer;text-decoration:underline;margin-left:.4rem}
.modal-bg{position:fixed;inset:0;background:rgba(10,16,22,.5);display:flex;align-items:center;justify-content:center;padding:1rem;z-index:100}
.modal-bg[hidden]{display:none}
.modal{background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,.4);width:100%;max-width:26rem;padding:1.2rem}
.modal h3{margin:0 0 .2rem;font-size:1rem}
.modal .msub{margin:0 0 .9rem;font-size:.8rem;color:var(--muted)}
.modal .clist{display:flex;flex-direction:column;gap:.1rem;max-height:16rem;overflow:auto;margin-bottom:1rem}
.modal label{display:flex;align-items:center;gap:.6rem;padding:.5rem;border-radius:7px;cursor:pointer;font-size:.9rem}
.modal label:hover{background:var(--surface-2)}
.modal label input{width:1.05rem;height:1.05rem;accent-color:var(--accent)}
.modal .mnone{color:var(--muted);font-size:.85rem;padding:.5rem}
.modal input.tin{width:100%;font:inherit;padding:.5rem .6rem;border:1px solid var(--line);border-radius:8px;background:var(--surface-2);color:var(--ink)}
.modal .mmsg{margin:0 0 1rem;font-size:.9rem;color:var(--muted)}
.srow{margin-bottom:.9rem}
.srow .slab{font-family:var(--mono);font-size:.64rem;letter-spacing:.03em;text-transform:uppercase;color:var(--faint);margin-bottom:.25rem}
.srow .sinline{display:flex;gap:.4rem;align-items:center}
.srow .sinline input.tin{flex:1;min-width:0}
.srow .sinline a.mini{text-decoration:none;display:inline-flex;align-items:center;white-space:nowrap}
.modal-actions{display:flex;justify-content:flex-end;gap:.5rem}
.console h2{font-family:var(--mono);font-size:.7rem;letter-spacing:.04em;text-transform:uppercase;color:var(--faint);margin:0 0 .4rem}
pre.log{font-family:var(--mono);font-size:.78rem;line-height:1.6;margin:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:.9rem 1.1rem;min-height:3.4rem;white-space:pre-wrap;word-break:break-word;color:var(--muted);box-shadow:var(--shadow)}
pre.log .ok{color:var(--pos-fg)}pre.log .warn{color:var(--crit-fg)}
@media(max-width:640px){
table,thead,tbody,tr,td{display:block}thead{display:none}
tbody tr{position:relative;border-bottom:1px solid var(--line);padding:.9rem 1.1rem}tbody tr:last-child{border-bottom:none}
tbody td{border:none;padding:.18rem 0}tbody td.c-name{font-size:1rem;padding-right:2.6rem}
tbody td.c-actions{position:absolute;top:.7rem;right:.9rem;margin:0;padding:0}
td[data-k]:not(.c-actions)::before{content:attr(data-k) "  ";font-family:var(--mono);font-size:.66rem;text-transform:uppercase;letter-spacing:.03em;color:var(--faint)}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style></head><body>
<div class="wrap">
<header class="top"><h1>design-share 管理コンソール</h1><span class="env" id="env"></span><a id="estlink" class="env" style="text-decoration:none;color:var(--accent)" href="#">コスト試算 →</a></header>
<p class="sub">公開中の全パターンを横断管理します。localhostのみ・本番非公開。操作はAWS認証情報で直接実行されます。</p>
<div class="summary">
<div class="stat"><div class="n" id="s-total">–</div><div class="k">総パターン</div></div>
<div class="stat pos"><div class="n" id="s-active">–</div><div class="k">公開中</div></div>
<div class="stat crit"><div class="n" id="s-disabled">–</div><div class="k">無効化済み</div></div>
</div>
<div class="panel"><div class="ph"><h2>全体ギャラリー</h2><span id="g-actions"></span></div>
<div class="gwrap" id="g-body"></div></div>
<div class="panel"><div class="ph"><h2>カテゴリ（名前付きギャラリー）</h2><button id="cat-new" class="mini">＋ 新規カテゴリ</button></div>
<div id="cat-body"></div></div>
<div class="panel"><div class="ph"><h2>パターン一覧</h2><span class="pfilter" id="pfilter"></span></div>
<table><thead><tr><th>パターン名</th><th>slug</th><th>状態</th><th>更新日</th><th>操作</th></tr></thead>
<tbody id="rows"><tr><td colspan="5" style="padding:1rem 1.1rem;color:var(--muted)">読み込み中…</td></tr></tbody></table></div>
<div class="console"><h2>操作ログ</h2><pre class="log" id="log">操作を選ぶと結果をここに表示します。</pre></div>
</div>
<div class="modal-bg" id="modal" hidden><div class="modal">
<h3 id="modal-title">　</h3>
<p class="msub" id="modal-sub"></p>
<div id="modal-body"></div>
<div class="modal-actions"><button id="modal-cancel" class="mini">閉じる</button><button id="modal-ok" class="mini primary">OK</button></div>
</div></div>
<script>
const TOKEN=new URLSearchParams(location.search).get('token')||'';
document.getElementById('estlink').href='/estimator?token='+encodeURIComponent(TOKEN);
const $=(id)=>document.getElementById(id);
const KEBAB='<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>';
let openMenu=null;let CATS=[];let modalSlug=null;let selCat=null;let DOMAIN='';
function closeMenu(){if(!openMenu)return;openMenu.menu.classList.remove('open');openMenu.trigger.setAttribute('aria-expanded','false');openMenu=null;}
document.addEventListener('click',closeMenu);
document.addEventListener('keydown',(e)=>{if(e.key==='Escape')closeMenu();});
function log(t,cls){const l=$('log');l.textContent='';const s=document.createElement('span');if(cls)s.className=cls;s.textContent=t;l.appendChild(s);}
async function api(path,opts){const r=await fetch(path,Object.assign({method:'POST',headers:{'X-Console-Token':TOKEN}},opts||{}));return{ok:r.ok,text:await r.text()};}
async function doOp(path,label){closeMenu();log(label+' 実行中…');const {ok,text}=await api(path);log(text.trim()||(ok?'完了':'失敗'),ok?'ok':'warn');refresh();}
function item(icon,label,cls,disabled,onClick){const b=document.createElement('button');b.type='button';b.className='item'+(cls?' '+cls:'');b.setAttribute('role','menuitem');if(disabled)b.disabled=true;
const ic=document.createElement('span');ic.className='ic';ic.textContent=icon;const lb=document.createElement('span');lb.textContent=label;b.append(ic,lb);
if(!disabled)b.addEventListener('click',(e)=>{e.stopPropagation();onClick();});return b;}
function menuButton(aria,items){const wrap=document.createElement('div');wrap.className='menu-wrap';
const trig=document.createElement('button');trig.type='button';trig.className='kebab';trig.innerHTML=KEBAB;
trig.setAttribute('aria-haspopup','true');trig.setAttribute('aria-expanded','false');trig.setAttribute('aria-label',aria);
const menu=document.createElement('div');menu.className='menu';menu.setAttribute('role','menu');items.forEach(x=>menu.appendChild(x));
trig.addEventListener('click',(e)=>{e.stopPropagation();const isOpen=openMenu&&openMenu.menu===menu;closeMenu();if(!isOpen){menu.classList.add('open');trig.setAttribute('aria-expanded','true');openMenu={menu,trigger:trig};}});
menu.addEventListener('click',(e)=>e.stopPropagation());wrap.append(trig,menu);return wrap;}
function sep(){const d=document.createElement('div');d.className='sep';return d;}

let modalOk=null;
function closeModal(){$('modal').hidden=true;modalOk=null;}
function openModal(title,sub,build,okLabel,onOk){
$('modal-title').textContent=title;const s=$('modal-sub');s.textContent=sub||'';s.style.display=sub?'':'none';
const body=$('modal-body');body.textContent='';build(body);
const ok=$('modal-ok');if(okLabel){ok.textContent=okLabel;ok.style.display='';}else{ok.style.display='none';}
modalOk=onOk;$('modal').hidden=false;const inp=body.querySelector('input.tin');if(inp&&!inp.readOnly){inp.focus();}}
function fallbackCopy(text,done){const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(ta);}
function doCopy(text,btn){const orig=btn.textContent;const done=()=>{btn.textContent='コピー済';setTimeout(()=>{btn.textContent=orig;},1200);};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(done,()=>fallbackCopy(text,done));}else fallbackCopy(text,done);}
function shareRow(label,value,isUrl){const wrap=document.createElement('div');wrap.className='srow';
const lab=document.createElement('div');lab.className='slab';lab.textContent=label;
const row=document.createElement('div');row.className='sinline';
const inp=document.createElement('input');inp.type='text';inp.className='tin';inp.readOnly=true;inp.value=value;inp.addEventListener('focus',()=>inp.select());
const copy=document.createElement('button');copy.type='button';copy.className='mini';copy.textContent='コピー';copy.addEventListener('click',()=>doCopy(value,copy));
row.append(inp,copy);
if(isUrl){const a=document.createElement('a');a.className='mini';a.href=value;a.target='_blank';a.rel='noopener';a.textContent='開く ↗';row.append(a);}
wrap.append(lab,row);return wrap;}
async function fetchToken(kind,id){const r=await fetch('/api/token?kind='+kind+'&id='+encodeURIComponent(id),{headers:{'X-Console-Token':TOKEN}});
if(!r.ok)throw new Error(await r.text());return (await r.json()).token||'';}
function openShare(title,url,kind,id){closeMenu();
let tokRow=null,loading=null;
openModal(title,'URLとトークンは別々のチャネルで共有相手へ渡してください。',(body)=>{
body.appendChild(shareRow('URL',url,true));
loading=document.createElement('p');loading.className='mmsg';loading.textContent='トークンを取得中…';body.appendChild(loading);
},null,null);
fetchToken(kind,id).then(token=>{
if(!loading||!loading.parentNode)return; // モーダルが閉じられていたら何もしない
if(token){tokRow=shareRow('トークン',token,false);loading.replaceWith(tokRow);}
else{loading.textContent='有効なトークンがありません（無効化中の可能性）。';}
}).catch(()=>{if(loading&&loading.parentNode)loading.textContent='トークンの取得に失敗しました。';});}
function openUrl(url){closeMenu();window.open(url,'_blank','noopener');}

function patternMenu(p){const items=[];const purl='https://'+DOMAIN+'/p/'+p.slug+'/';
items.push(item('↗','開く','',false,()=>openUrl(purl)));
items.push(item('🔗','共有（URL・トークン）','',false,()=>openShare(p.name,purl,'pattern',p.slug)));
items.push(sep());
items.push(item('↓','エクスポート','',false,()=>doOp('/api/export?slug='+encodeURIComponent(p.slug),'export')));
items.push(item('✎','名前を変更','',false,()=>renamePattern(p)));
items.push(item('▦','カテゴリを編集','',false,()=>openMembership(p)));
if(p.status==='active'){
items.push(item('⟳','トークンを再発行','',false,()=>doOp('/api/rotate?slug='+encodeURIComponent(p.slug),'rotate')));
items.push(sep());
items.push(item('⦸','無効化する','danger',false,()=>{if(confirm('「'+p.name+'」を無効化しますか？\n（先にエクスポートを実行します。データは残り、あとで再公開できます）'))doOp('/api/invalidate?slug='+encodeURIComponent(p.slug),'disable');}));
}else{
items.push(sep());
items.push(item('▲','再公開する（新トークン）','good',false,()=>doOp('/api/rotate?slug='+encodeURIComponent(p.slug),'republish')));
}
return menuButton(p.name+' の操作メニュー',items);}

function renamePattern(p){closeMenu();const name=prompt('新しい表示名を入力してください',p.name);if(name===null)return;const t=name.trim();if(!t){log('名前が空です。変更を中止しました。','warn');return;}
doOp('/api/rename?slug='+encodeURIComponent(p.slug)+'&name='+encodeURIComponent(t),'rename');}

function createCategory(){closeMenu();const name=prompt('新しいカテゴリ名を入力してください');if(name===null)return;const t=name.trim();if(!t){log('名前が空です。','warn');return;}doOp('/api/gallery-create?name='+encodeURIComponent(t),'gallery create');}

function catSelectRow(caret,name,count,selected,onSelect,pillStatus,menu){
const row=document.createElement('div');row.className='catrow'+(selected?' sel':'');
const nm=document.createElement('span');nm.className='cname';
const car=document.createElement('span');car.className='caret';car.textContent=caret;
const tx=document.createElement('span');tx.textContent=name;nm.append(car,tx);row.append(nm);
if(pillStatus){const pill=document.createElement('span');pill.className='pill '+(pillStatus==='enabled'?'active':pillStatus==='disabled'?'disabled':'unset');pill.style.flex='none';pill.textContent=pillStatus==='enabled'?'有効':pillStatus==='disabled'?'無効':'トークン無';row.append(pill);}
const cnt=document.createElement('span');cnt.className='cmeta';cnt.textContent=count;row.append(cnt);
if(menu){const a=document.createElement('span');a.className='cactions';a.appendChild(menu);row.append(a);}
row.addEventListener('click',onSelect);return row;}
function renderCategories(cats,total){const body=$('cat-body');body.textContent='';
body.appendChild(catSelectRow('▤','すべてのパターン',total+'件',selCat===null,()=>{selCat=null;refresh();},null,null));
if(!cats.length){const d=document.createElement('div');d.className='cempty';d.textContent='カテゴリはまだありません。「＋ 新規カテゴリ」で作成できます。';body.appendChild(d);return;}
cats.forEach(c=>{
const items=[
item('↗','開く','',false,()=>openUrl(c.url)),
item('🔗','共有（URL・トークン）','',false,()=>openShare(c.name||c.gslug,c.url,'gallery',c.gslug)),
sep(),
item('⟳','共有トークンを再発行','',false,()=>doOp('/api/gallery-rotate?gslug='+encodeURIComponent(c.gslug),'gallery rotate')),
item(c.status==='disabled'?'▲':'⦸',c.status==='disabled'?'再有効化':'無効化',c.status==='disabled'?'good':'danger',false,()=>doOp((c.status==='disabled'?'/api/gallery-rotate':'/api/gallery-disable')+'?gslug='+encodeURIComponent(c.gslug),'gallery')),
sep(),
item('×','削除','danger',false,()=>{if(confirm('カテゴリ「'+(c.name||c.gslug)+'」を削除しますか？\n所属は全解除されますが、パターン自体は残ります。'))doOp('/api/gallery-delete?gslug='+encodeURIComponent(c.gslug),'gallery delete');}),
];
body.appendChild(catSelectRow('▸',c.name||c.gslug,c.count+'件',selCat===c.gslug,()=>{selCat=c.gslug;refresh();},c.status,menuButton((c.name||c.gslug)+' の操作',items)));});}

function openMembership(p){closeMenu();
openModal('カテゴリを編集',p.name,(body)=>{
const list=document.createElement('div');list.className='clist';
if(!CATS.length){const d=document.createElement('div');d.className='mnone';d.textContent='カテゴリがありません。先に「＋ 新規カテゴリ」で作成してください。';list.appendChild(d);}
else CATS.forEach(c=>{const lab=document.createElement('label');const cb=document.createElement('input');cb.type='checkbox';cb.value=c.gslug;cb.checked=(p.galleries||[]).indexOf(c.gslug)>=0;const sp=document.createElement('span');sp.textContent=c.name||c.gslug;lab.append(cb,sp);list.appendChild(lab);});
body.appendChild(list);
},'保存',async()=>{
const gs=Array.prototype.slice.call($('modal-body').querySelectorAll('input[type=checkbox]:checked')).map(x=>x.value);
closeModal();log('カテゴリ所属を更新中…');
const {ok,text}=await api('/api/pattern-galleries?slug='+encodeURIComponent(p.slug)+'&galleries='+encodeURIComponent(gs.join(',')));
log(text.trim()||(ok?'完了':'失敗'),ok?'ok':'warn');refresh();});}

function galleryControls(g){
const box=$('g-actions');box.textContent='';const body=$('g-body');body.textContent='';
const pill=document.createElement('span');pill.className='pill '+(g.status==='enabled'?'active':g.status==='disabled'?'disabled':'unset');
pill.textContent=g.status==='enabled'?'有効':g.status==='disabled'?'無効化済み':'未設定';box.appendChild(pill);
const items=[];
if(g.status==='enabled'){
const url=document.createElement('a');url.className='gurl';url.href=g.url;url.target='_blank';url.rel='noopener';url.textContent=g.url;body.appendChild(url);
items.push(item('↗','開く','',false,()=>openUrl(g.url)));
items.push(item('🔗','共有（URL・トークン）','',false,()=>openShare('全体ギャラリー',g.url,'global','')));
items.push(sep());
items.push(item('⟳','共通トークンを再発行','',false,()=>doOp('/api/gallery?op=rotate','gallery rotate')));
items.push(sep());
items.push(item('⦸','ギャラリーを無効化','danger',false,()=>{if(confirm('共有ギャラリーを無効化しますか？\n（各パターンの個別URLには影響しません）'))doOp('/api/gallery?op=disable','gallery disable');}));
}else{
const msg=document.createElement('span');msg.className='goff';msg.textContent=g.status==='disabled'?'無効化済み。有効化すると同じURLで再開します。':'未設定。有効化すると1つのURL＋共通トークンで全パターンを横断閲覧できます。';body.appendChild(msg);
items.push(item('▲','ギャラリーを有効化','good',false,()=>doOp('/api/gallery?op=init','gallery init')));
}
$('g-actions').appendChild(menuButton('共有ギャラリーの操作メニュー',items));
}

function renderRows(patterns,emptyMsg){const tb=$('rows');tb.textContent='';
if(!patterns.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=5;td.style.padding='1rem 1.1rem';td.style.color='var(--muted)';td.textContent=emptyMsg||'まだデプロイされたパターンはありません。';tr.appendChild(td);tb.appendChild(tr);return;}
patterns.forEach(p=>{const tr=document.createElement('tr');
const n=document.createElement('td');n.className='c-name name';n.textContent=p.name||p.slug;
const s=document.createElement('td');s.className='slug';s.dataset.k='slug';s.textContent=p.slug;
const st=document.createElement('td');st.dataset.k='状態';const pill=document.createElement('span');pill.className='pill '+(p.status==='active'?'active':'disabled');pill.textContent=p.status==='active'?'公開中':'無効化済み';st.appendChild(pill);
const d=document.createElement('td');d.className='date';d.dataset.k='更新';d.textContent=(p.updatedAt||'').slice(0,10);
const a=document.createElement('td');a.className='c-actions';a.dataset.k='操作';a.appendChild(patternMenu(p));
tr.append(n,s,st,d,a);tb.appendChild(tr);});}

async function refresh(){const r=await fetch('/api/state',{headers:{'X-Console-Token':TOKEN}});
if(!r.ok){log('状態の取得に失敗: '+(await r.text()).trim(),'warn');return;}
const data=await r.json();
DOMAIN=(data.gallery.url||'').replace('https://','').replace('/gallery/','');
$('env').textContent='env: '+DOMAIN;
const ps=data.patterns||[];$('s-total').textContent=ps.length;
$('s-active').textContent=ps.filter(p=>p.status==='active').length;
$('s-disabled').textContent=ps.filter(p=>p.status!=='active').length;
galleryControls(data.gallery||{status:'unset',url:''});
CATS=data.categories||[];
if(selCat!==null && !CATS.some(c=>c.gslug===selCat)) selCat=null;
renderCategories(CATS,ps.length);
const cat=selCat!==null?CATS.find(c=>c.gslug===selCat):null;
const shown=cat?ps.filter(p=>(p.galleries||[]).indexOf(selCat)>=0):ps;
const pf=$('pfilter');pf.textContent='';
if(cat){pf.appendChild(document.createTextNode('絞り込み: '+(cat.name||cat.gslug)));const cl=document.createElement('span');cl.className='clear';cl.textContent='すべて表示';cl.addEventListener('click',()=>{selCat=null;refresh();});pf.appendChild(cl);}
renderRows(shown,cat?'このカテゴリに所属するパターンはありません。パターンの⋮「カテゴリを編集」で追加できます。':'');}
$('cat-new').addEventListener('click',createCategory);
$('modal-cancel').addEventListener('click',closeModal);
$('modal-ok').addEventListener('click',()=>{if(modalOk)modalOk();});
$('modal').addEventListener('click',(e)=>{if(e.target===$('modal'))closeModal();});
document.addEventListener('keydown',(e)=>{if(e.key==='Escape'&&!$('modal').hidden)closeModal();});
refresh();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, ctype: str = "text/plain; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def do_GET(self) -> None:
        if not self._host_ok():
            self._send(403, "forbidden")
            return
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/state":
            # /api/state は現在トークンを含む秘密を返すため、変更系と同じくトークン必須
            if self.headers.get("X-Console-Token", "") != CONSOLE_TOKEN:
                self._send(403, "invalid console token")
                return
            try:
                body = json.dumps(state(), ensure_ascii=False)
            except Exception as e:  # 認証/権限エラー等は500で表面化（0件に化けさせない）
                self._send(500, f"状態の取得に失敗しました（AWS認証・権限・バケット名を確認）: {e}")
                return
            self._send(200, body, "application/json; charset=utf-8")
        elif path == "/api/pricing":
            if self.headers.get("X-Console-Token", "") != CONSOLE_TOKEN:
                self._send(403, "invalid console token")
                return
            self._send(200, json.dumps(pricing(), ensure_ascii=False), "application/json; charset=utf-8")
        elif path == "/api/token":
            # 共有メニューを開いたときだけトークンの実値をオンデマンド取得する（一覧では取得しない）
            if self.headers.get("X-Console-Token", "") != CONSOLE_TOKEN:
                self._send(403, "invalid console token")
                return
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            kind = (qs.get("kind") or [""])[0]
            ident = (qs.get("id") or [""])[0]
            if kind not in ("pattern", "gallery", "global"):
                self._send(400, "kindはpattern/gallery/globalのいずれか")
                return
            if kind != "global" and not SLUG_RE.match(ident):
                self._send(400, "idの形式が不正です")
                return
            try:
                tok = fetch_token_for(kind, ident)
            except Exception as e:
                self._send(500, f"トークンの取得に失敗しました: {e}")
                return
            self._send(200, json.dumps({"token": tok}, ensure_ascii=False), "application/json; charset=utf-8")
        elif path == "/estimator":
            try:
                with open(os.path.join(SCRIPT_DIR, "..", "references", "templates", "estimator.html"), encoding="utf-8") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, "estimator template not found")
        else:
            self._send(404, "not found")

    def do_POST(self) -> None:
        if not self._host_ok():
            self._send(403, "forbidden")
            return
        if self.headers.get("X-Console-Token", "") != CONSOLE_TOKEN:
            self._send(403, "invalid console token")
            return
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        slug = q.get("slug", [""])[0]

        # 全体ギャラリー操作（slug不要）
        if parsed.path == "/api/gallery":
            op = q.get("op", [""])[0]
            if op not in {"init", "rotate", "disable"}:
                self._send(400, "invalid gallery op")
                return
            ok, output = run_script("gallery", op)
            self._send(200 if ok else 500, output)
            return

        # 名前付きギャラリー（カテゴリ）操作
        if parsed.path == "/api/gallery-create":
            name = q.get("name", [""])[0].strip()
            if not name or len(name) > 80 or any(ord(c) < 0x20 for c in name):
                self._send(400, "invalid name")
                return
            ok, output = run_script("galleries", "create", name)
            self._send(200 if ok else 500, output)
            return
        if parsed.path in ("/api/gallery-rotate", "/api/gallery-disable", "/api/gallery-delete"):
            gslug = q.get("gslug", [""])[0]
            if not SLUG_RE.match(gslug):
                self._send(400, "invalid gslug")
                return
            sub = {"/api/gallery-rotate": "rotate", "/api/gallery-disable": "disable",
                   "/api/gallery-delete": "delete"}[parsed.path]
            ok, output = run_script("galleries", sub, gslug)
            self._send(200 if ok else 500, output)
            return
        if parsed.path == "/api/pattern-galleries":
            slug = q.get("slug", [""])[0]
            if not SLUG_RE.match(slug):
                self._send(400, "invalid slug")
                return
            gslugs = [g for g in q.get("galleries", [""])[0].split(",") if g]
            if any(not SLUG_RE.match(g) for g in gslugs):
                self._send(400, "invalid gslug")
                return
            ok, output = run_script("galleries", "set", slug, *gslugs)
            self._send(200 if ok else 500, output)
            return

        # 以降はパターン単位の操作。slug必須。
        if not SLUG_RE.match(slug):
            self._send(400, "invalid slug")
            return
        if parsed.path == "/api/rename":
            name = q.get("name", [""])[0].strip()
            if not name or len(name) > 80 or any(ord(c) < 0x20 for c in name):
                self._send(400, "invalid name")
                return
            ok, output = run_script("rename", slug, name)
            self._send(200 if ok else 500, output)
            return
        actions = {
            "/api/export": ("export", [slug]),
            "/api/rotate": ("rotate", [slug]),
            "/api/invalidate": ("disable", [slug]),
        }
        if parsed.path not in actions:
            self._send(404, "not found")
            return
        script, args = actions[parsed.path]
        ok, output = run_script(script, *args)
        self._send(200 if ok else 500, output)

    def log_message(self, fmt: str, *args) -> None:  # 静かに
        pass


if __name__ == "__main__":
    print(f"design-share console: http://{HOST}:{PORT}/?token={CONSOLE_TOKEN}")
    print("（このURLごと開いてください。tokenが無いと操作は403になります。Ctrl+Cで終了）")
    http.server.ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

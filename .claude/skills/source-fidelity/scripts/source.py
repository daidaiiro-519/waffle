# -*- coding: utf-8 -*-
"""調査対象の原文を落とし、識別子が原文に在るかを文字列で検める。

  python3 source.py fetch  <URL> [--dir <保存先>]
  python3 source.py verify <保存したファイル または フォルダ> <識別子> [<識別子>...]
                           [--near <アンカーの語>] [--within <行数>]
  python3 source.py verify <保存したファイル> --from <識別子を1行1個で書いたファイル>
  python3 source.py list   [--dir <保存先>]

**要約を経由して識別子を取ってはいけない。**
項目名は説明ではなく鍵である。1文字違えば、その鍵で引く実装は必ず空を返す。
空が返ることと、その事象が起きなかったことは、あとから区別できない。

実際に起きたこと（2026-09-05）——
公式ページを要約させて読み、要約したモデルが項目名を言い換えた。
`config_source` ・ `setup_type` ・ `expanded_prompt` ・ `user_input` の4つは
原文に1度も出てこない名前だった。それを根拠に「公式と実物が食い違う」と結論した。
原文で照合し直すと、15事象すべてが一致した。誤っていたのは読み方だった。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

DEFAULT_DIR = "07-appendix/sources"
UA = "Mozilla/5.0"


def slug(url):
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return s[:120]


def fetch(url, outdir):
    """原文を落とす。まず <URL>.md を試し、無ければ本体を取る。"""
    os.makedirs(outdir, exist_ok=True)
    tried = []
    for cand in ([url] if url.endswith((".md", ".txt", ".json")) else [url + ".md", url]):
        path = os.path.join(outdir, slug(cand))
        r = subprocess.run(
            ["curl", "-sSL", "-m", "60", "-A", UA, cand, "-o", path,
             "-w", "%{http_code} %{content_type}"],
            capture_output=True, text=True)
        code = (r.stdout or "").split(" ")[0]
        ctype = (r.stdout or " ").split(" ", 1)[-1].strip()
        size = os.path.getsize(path) if os.path.exists(path) else 0
        tried.append((cand, code, ctype, size))
        if code == "200" and size > 0 and "html" not in ctype:
            body = open(path, "rb").read()
            meta = {
                "url": cand,
                "requested": url,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "lines": body.count(b"\n") + 1,
                "content_type": ctype,
            }
            with open(path + ".meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1)
            print(f"落とした: {path}")
            print(f"  {meta['bytes']:,} バイト ・ {meta['lines']:,} 行 ・ {ctype}")
            print(f"  sha256 {meta['sha256'][:16]}…")
            return path
    print("落とせなかった。試したもの:")
    for c, code, ctype, size in tried:
        print(f"  {code}  {size:>9,}  {ctype[:30]:32}{c}")
    print("\nHTML しか返らない場合でも、要約させて読んではいけない。"
          "\n本文を保存し、識別子はその文字列で照合する。")
    return None


SKIP = {".git", "node_modules", "target", "dist", "build", ".venv", "__pycache__"}


def load(path):
    """原文を読む。フォルダなら、その下の文字ファイルを全部つなぐ。"""
    if os.path.isfile(path):
        return open(path, encoding="utf-8", errors="replace").read(), 1
    buf, n = [], 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.getsize(fp) > 4_000_000:
                    continue
                buf.append(open(fp, encoding="utf-8", errors="replace").read())
                n += 1
            except OSError:
                pass
    return "\n".join(buf), n


def where(path, name, limit=2):
    """その識別子が、どのファイルの何行目に在るかを出す。"""
    out = []
    if os.path.isfile(path):
        for i, ln in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            if name in ln:
                out.append(f"{os.path.basename(path)}:{i}")
                if len(out) >= limit:
                    break
        return out
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.getsize(fp) > 4_000_000:
                    continue
                for i, ln in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                    if name in ln:
                        out.append(f"{os.path.relpath(fp, path)}:{i}")
                        break
            except OSError:
                pass
            if len(out) >= limit:
                return out
    return out


def verify(path, names, near=None, within=40):
    """識別子が原文に在るかを、文字列そのままで検める。

    near を渡すと、その語から within 行の内側に在るかまで見る。
    **名前が在ることと、その名前がそこで使われることは別である。**
    """
    if not os.path.exists(path):
        print(f"× 原文が無い: {path}")
        return 1
    text, nfiles = load(path)
    meta_path = path + ".meta.json"
    if os.path.exists(meta_path):
        m = json.load(open(meta_path, encoding="utf-8"))
        print(f"── {m['url']}")
        print(f"   {m['bytes']:,} バイト ・ {m['lines']:,} 行 ・ 落とした日 {m['fetched_at'][:10]}")
    elif os.path.isdir(path):
        print(f"── {path}  {nfiles:,} ファイル ・ {len(text):,}字")
    else:
        print(f"── {path}  {len(text):,}字")
    lines = text.split("\n")
    anchors = [i for i, ln in enumerate(lines) if near and near in ln] if near else []
    if near:
        print(f"   アンカー「{near}」 {len(anchors)} か所　その ±{within} 行の内側を見る")
    miss = []
    for n in names:
        c = text.count(n)
        if not c:
            print(f"  ×    {n:34} 原文に無い")
            miss.append(n)
            continue
        if near:
            hit = [i for i, ln in enumerate(lines) if n in ln]
            close = any(abs(h - a) <= within for h in hit for a in anchors)
            if not close:
                print(f"  ×    {n:34} {c} か所に在るが、アンカーの近くに無い")
                miss.append(n)
                continue
        loc = where(path, n)
        print(f"  ok   {n:34} {c} か所" + (f"　{' ・ '.join(loc)}" if loc else ""))
    print(f"── 照合 {len(names)} ／ 原文に無い {len(miss)}")
    if miss:
        print("\n**原文に無い識別子を、原典の名前として書いてはいけない。**")
        print("見つからない原因は3つ——①名前を言い換えた ②別のページに在る ③本当に無い。")
        print("①なら直す。②なら該当ページを落として照合し直す。"
              "③なら「無い」と書く。**推測で埋めない。**")
    return 1 if miss else 0


def lst(outdir):
    if not os.path.isdir(outdir):
        print(f"まだ何も落としていない: {outdir}")
        return 0
    rows = []
    for f in sorted(os.listdir(outdir)):
        if f.endswith(".meta.json"):
            m = json.load(open(os.path.join(outdir, f), encoding="utf-8"))
            rows.append((m["fetched_at"][:10], m["lines"], m["url"]))
    print(f"{'落とした日':12}{'行':>8}  出どころ")
    for d, l, u in rows:
        print(f"{d:12}{l:>8,}  {u}")
    print(f"── {len(rows)} 件")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    outdir = DEFAULT_DIR
    if "--dir" in args:
        i = args.index("--dir")
        outdir = args[i + 1]
        del args[i:i + 2]
    if cmd == "fetch":
        sys.exit(0 if fetch(args[0], outdir) else 1)
    if cmd == "verify":
        path = args[0]
        if "--from" in args:
            i = args.index("--from")
            names = [x.strip() for x in open(args[i + 1], encoding="utf-8") if x.strip()]
        else:
            names = args[1:]
        near, within = None, 40
        if "--near" in args:
            i = args.index("--near"); near = args[i + 1]; del args[i:i + 2]
        if "--within" in args:
            i = args.index("--within"); within = int(args[i + 1]); del args[i:i + 2]
        names = [x for x in args[1:] if not x.startswith("--")] if "--from" not in sys.argv else names
        if not names:
            print("照合する識別子を渡す")
            sys.exit(2)
        sys.exit(verify(path, names, near, within))
    if cmd == "list":
        sys.exit(lst(outdir))
    print(__doc__)
    sys.exit(2)

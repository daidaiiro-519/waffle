"""graph_index — 契約（MD frontmatter ⇄ HTML <meta>、本文リンク＝edge）に沿って
sources/配下を再帰スキャンし、node/edgeのグラフを組み立てる。

契約（brainstorm-document-graph-skill.md 論点1の合意決定）:
  - node属性は id/type/title/description/tags の4項目。id はファイル名（拡張子除く）。
    MDは frontmatter（`---` で挟まれた平坦な `key: value`。tags のような配列は
    `["a", "b"]` または `- a` 形式のどちらかに対応する最小YAMLパーサでよい）。
    HTMLは `<meta name="...">` から同じ4項目を読む。
  - edge は本文中の標準リンク（MD `[text](target)` / HTML `<a href="target">`）の
    target を、相対パスとしてではなくファイル名（拡張子除く）をIDとして全ソース
    横断で一致検索して解決する（Waffleのdocument.json解決方式・Obsidianのwikilink
    解決方式と同型）。
  - ファイル名は全ソースを通じて一意という制約を持つ。重複はスキャン時に検出し、
    重複したidは（曖昧なため）edge解決の対象から外し、duplicatesとして報告する。

外部依存ゼロ（PyYAML不要）。標準ライブラリのみで完結させる。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

_FRONTMATTER_RE = re.compile(r"^\s*---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_HTML_LINK_RE = re.compile(r'<a\b[^>]*\bhref\s*=\s*"([^"]+)"', re.IGNORECASE)
_HTML_META_RE = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
_HTML_META_ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')
_HTML_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_MD_HEADING_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)

CONTRACT_FIELDS = ("type", "title", "description", "tags")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_inline_list(text: str) -> list[str]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(v) for v in parsed]
    except (json.JSONDecodeError, ValueError):
        pass
    inner = text.strip("[]")
    return [_strip_quotes(v) for v in inner.split(",") if v.strip()]


def parse_frontmatter_block(block_text: str) -> dict:
    """`---`で挟まれた中身（末尾の`---`を含まない）を、平坦な`key: value`＋
    配列（インラインまたは`- item`形式）だけをサポートする最小パーサで読む。"""
    lines = block_text.split("\n")
    result: dict = {}
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if ":" not in line or line.lstrip().startswith("-"):
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            i += 1
            continue
        if rest.startswith("["):
            result[key] = _parse_inline_list(rest)
            i += 1
            continue
        if rest == "":
            items = []
            j = i + 1
            while j < n and lines[j].strip().startswith("- "):
                items.append(_strip_quotes(lines[j].strip()[2:]))
                j += 1
            if items:
                result[key] = items
                i = j
            else:
                result[key] = ""
                i += 1
            continue
        result[key] = _strip_quotes(rest)
        i += 1
    return result


def parse_md(text: str) -> tuple[dict, str]:
    """MDテキストから(frontmatter辞書, 本文)を返す。frontmatterが無ければ({}, text)。"""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    frontmatter = parse_frontmatter_block(m.group(1))
    body = text[m.end():]
    return frontmatter, body


def parse_html_meta(text: str) -> dict:
    """HTMLテキストから`<meta name="..." content="...">`と`<title>`をcontract属性へ写像する。"""
    meta: dict = {}
    for tag in _HTML_META_RE.findall(text):
        attrs = dict(_HTML_META_ATTR_RE.findall(tag))
        name = attrs.get("name")
        if not name or name not in CONTRACT_FIELDS:
            continue
        content = attrs.get("content", "")
        if name == "tags":
            meta[name] = [t.strip() for t in content.split(",") if t.strip()]
        else:
            meta[name] = content
    if "title" not in meta:
        m = _HTML_TITLE_RE.search(text)
        if m:
            meta["title"] = re.sub(r"\s+", " ", m.group(1)).strip()
    return meta


def _extract_md_links(body: str) -> list[str]:
    return _MD_LINK_RE.findall(body)


def _extract_html_links(text: str) -> list[str]:
    return _HTML_LINK_RE.findall(text)


def _target_to_id(target: str) -> str | None:
    target = target.strip()
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.scheme in ("http", "https", "mailto", "tel"):
        return None
    path = parsed.path
    if not path:
        return None
    stem = Path(path).stem
    return stem or None


def _node_from_md(path: Path, node_id: str) -> tuple[dict, list[str], str]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_md(text)
    title = frontmatter.get("title")
    if not title:
        heading = _MD_HEADING_RE.search(body)
        title = heading.group(1).strip() if heading else node_id
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    node = {
        "id": node_id,
        "type": frontmatter.get("type", ""),
        "title": title,
        "description": frontmatter.get("description", ""),
        "tags": tags,
        "hasContract": bool(frontmatter),
    }
    links = _extract_md_links(body)
    return node, links, body


def _node_from_html(path: Path, node_id: str) -> tuple[dict, list[str], str]:
    text = path.read_text(encoding="utf-8")
    meta = parse_html_meta(text)
    tags = meta.get("tags", [])
    node = {
        "id": node_id,
        "type": meta.get("type", ""),
        "title": meta.get("title") or node_id,
        "description": meta.get("description", ""),
        "tags": tags,
        "hasContract": bool(meta),
    }
    links = _extract_html_links(text)
    return node, links, text


def _build_mention_regex(ids_sorted_desc: list[str]) -> re.Pattern | None:
    """既知のID群を、長い順に並べた単語境界一致の正規表現へまとめる。長い順にする
    ことで、'uc-render-document-viewer' 中に含まれる 'uc-render-document' を
    部分一致で誤検出しない（re.finditer/findallは同じ開始位置でalternationの
    先頭から順に試すため、長い候補を先に置けば貪欲に長い方が優先される）。"""
    if not ids_sorted_desc:
        return None
    pattern = "|".join(re.escape(i) for i in ids_sorted_desc)
    return re.compile(rf"\b(?:{pattern})\b")


def _extract_mentions(text: str, mention_re: re.Pattern | None) -> list[str]:
    """本文中に、Markdownリンク/`<a href>`の形を取らない素のテキストとして書かれた
    既知ID（例: 箇条書きの'- uc-render-document'）も、ファイル名ID解決の対象として
    エッジ候補に含める。相対パスの有無に関わらず、ID文字列そのものが本文中に
    現れていれば紐づく、という設計（Waffleのレンダリングが実際のハイパーリンクを
    出力しているかどうかに依存しない）。"""
    if mention_re is None:
        return []
    return mention_re.findall(text)


def scan_sources(sources_root: Path, sources: list[dict]) -> dict:
    """sources（config.jsonのsources配列）が宣言した各aliasについて、
    sources_root/{alias}配下を`**/*.md`・`**/*.html`で再帰スキャンし、
    {"nodes": [...], "edges": [...], "duplicates": {id: [path,...]}, "warnings": [...]}
    を返す。"""
    all_files: list[tuple[Path, str, str]] = []  # (path, node_id, alias)
    for source in sources:
        alias = source["alias"]
        base = sources_root / alias
        if not base.exists():
            continue
        for pattern in ("*.md", "*.html"):
            for file_path in sorted(base.rglob(pattern)):
                if not file_path.is_file():
                    continue
                all_files.append((file_path, file_path.stem, alias))

    by_id: dict[str, list[tuple[Path, str]]] = {}
    for file_path, node_id, alias in all_files:
        by_id.setdefault(node_id, []).append((file_path, alias))

    duplicates = {node_id: [str(p) for p, _ in paths] for node_id, paths in by_id.items() if len(paths) > 1}

    nodes: list[dict] = []
    links_by_id: dict[str, list[str]] = {}
    bodies_by_id: dict[str, str] = {}
    contract_missing: dict[str, int] = {}
    contract_total: dict[str, int] = {}
    for node_id, paths in by_id.items():
        # 重複IDは曖昧なため、最初の1件のみをグラフに採用する（duplicatesで報告済み）。
        file_path, alias = sorted(paths, key=lambda pa: str(pa[0]))[0]
        contract_total[alias] = contract_total.get(alias, 0) + 1
        if file_path.suffix == ".md":
            node, links, body = _node_from_md(file_path, node_id)
        else:
            node, links, body = _node_from_html(file_path, node_id)
        if not node.pop("hasContract"):
            contract_missing[alias] = contract_missing.get(alias, 0) + 1
        node["href"] = f"{alias}/{file_path.relative_to(sources_root / alias).as_posix()}"
        node["sourceAlias"] = alias
        node["format"] = file_path.suffix.lstrip(".")
        nodes.append(node)
        links_by_id[node_id] = links
        bodies_by_id[node_id] = body

    known_ids = {n["id"] for n in nodes}
    # 本文中に正式なリンクの形を取らない素のID（例: 箇条書きの'- uc-render-document'）が
    # あれば、それもエッジ候補に含める（document-graph側だけで完結する解決）。
    mention_re = _build_mention_regex(sorted(known_ids, key=len, reverse=True))
    for node_id, body in bodies_by_id.items():
        links_by_id[node_id].extend(_extract_mentions(body, mention_re))

    edges = []
    seen_edges = set()
    for node_id, links in links_by_id.items():
        for target in links:
            target_id = _target_to_id(target)
            if not target_id or target_id == node_id or target_id not in known_ids:
                continue
            edge_key = (node_id, target_id)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append({"from": node_id, "to": target_id})

    warnings = []
    if duplicates:
        for dup_id, paths in duplicates.items():
            warnings.append(f"ファイル名の重複: '{dup_id}' が{len(paths)}件見つかりました（{', '.join(paths)}）。最初の1件のみグラフへ採用しました。")

    return {
        "nodes": nodes,
        "edges": edges,
        "duplicates": duplicates,
        "warnings": warnings,
        "contractMissing": contract_missing,
        "contractTotal": contract_total,
    }


def compute_categories(graph: dict) -> list[dict]:
    """全nodeを契約の`type`別にフラットなカテゴリへ分類する。各documentには、
    どちらの向きのedgeでも繋がる相手を"related"として（相手のカテゴリラベル付きで）
    あらかじめ埋め込む（カテゴリ選択→個別document選択→紐づく相手を見る、という
    ドリルダウンUXのため。relatedをカテゴリ別に折りたたむツリーとして描画するのは
    呼び出し側 graph_viewer_html_template の責務）。
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    def _label(n: dict) -> str:
        return n["type"] or "(未分類)"

    related: dict[str, set[str]] = {}
    for e in graph["edges"]:
        related.setdefault(e["from"], set()).add(e["to"])
        related.setdefault(e["to"], set()).add(e["from"])

    groups: dict[str, dict] = {}
    for n in graph["nodes"]:
        label = _label(n)
        key = f"cat::{label}"
        groups.setdefault(key, {"key": key, "label": label, "count": 0, "docs": []})
        groups[key]["count"] += 1
        related_items = sorted(
            (
                {"id": rid, "title": nodes_by_id[rid]["title"], "category": _label(nodes_by_id[rid])}
                for rid in related.get(n["id"], set()) if rid in nodes_by_id
            ),
            key=lambda r: (r["category"], r["title"]),
        )
        groups[key]["docs"].append({
            "id": n["id"],
            "title": n["title"],
            "description": n["description"],
            "href": n["href"],
            "format": n.get("format") or ("html" if n["href"].endswith(".html") else "md"),
            "related": related_items,
        })

    for g in groups.values():
        g["docs"].sort(key=lambda d: d["title"])
    return sorted(groups.values(), key=lambda g: -g["count"])

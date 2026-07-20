"""config.py — document-graph Skillのconfig.json（表示したいソースの宣言）を
読み書きし、宣言に対応するsymlinkをsources/配下へ同期する。

契約（brainstorm-document-graph-skill.md 論点2の合意決定）:
  - config.jsonは手作業編集を前提とせず、`document-graph add/list/remove`という
    CLI操作の結果として生成される状態ファイルとして扱う。
  - 構造は最小: {"sources": [{"alias": str, "path": str, "format": "md"|"html"}]}。
  - フォルダ正規化はSkill配下の統制フォルダ（sources/{alias}/）へ、外部の実フォルダを
    シムリンクで「持ち込む」向き（逆向きは採用しない）。alias単位でフォルダそのもの
    へ1本のシムリンクを張れば足りる。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = SKILL_ROOT / "config.json"
DEFAULT_SOURCES_DIR = SKILL_ROOT / "sources"

_ALIAS_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_-]+")


class ConfigError(Exception):
    pass


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {"sources": []}
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("sources", [])
    return data


def save_config(config: dict, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _sanitize_alias(name: str) -> str:
    sanitized = _ALIAS_SANITIZE_RE.sub("-", name).strip("-")
    return sanitized or "source"


def auto_alias(path: Path, existing: set[str]) -> str:
    """フォルダ名からaliasを自動生成する。衝突時のみ連番で解決する。"""
    base = _sanitize_alias(path.name)
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def detect_format(path: Path) -> str:
    """配下拡張子の多数決でformat（md/html）を推定する。単一ファイルならその拡張子。"""
    if path.is_file():
        return "html" if path.suffix.lower() == ".html" else "md"
    md_count = sum(1 for _ in path.rglob("*.md"))
    html_count = sum(1 for _ in path.rglob("*.html"))
    return "html" if html_count > md_count else "md"


def list_sources(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict]:
    return load_config(config_path)["sources"]


def _sync_one(alias: str, target: Path, sources_dir: Path) -> str:
    link = sources_dir / alias
    sources_dir.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        try:
            current_resolved = link.resolve()
        except OSError:
            current_resolved = None
        if current_resolved == target.resolve():
            return "unchanged"
        link.unlink()
        link.symlink_to(target, target_is_directory=target.is_dir())
        return "relinked"
    if link.exists():
        # symlinkでない何か（既存の実ディレクトリ/ファイル）があるのは統制フォルダの
        # 前提が崩れている状態なので、上書きせずbrokenとして報告する。
        return "conflict"
    if not target.exists():
        return "missing_target"
    link.symlink_to(target, target_is_directory=target.is_dir())
    return "created"


def sync_symlinks(config: dict, sources_dir: Path = DEFAULT_SOURCES_DIR) -> dict[str, str]:
    """config["sources"]の宣言に対して、sources_dir配下のsymlinkを差分同期する。
    宣言に無いaliasの古いsymlinkは削除する。各aliasのステータス
    （created/relinked/unchanged/missing_target/conflict）を返す。"""
    status: dict[str, str] = {}
    declared_aliases = {s["alias"] for s in config["sources"]}
    for source in config["sources"]:
        target = Path(source["path"])
        status[source["alias"]] = _sync_one(source["alias"], target, sources_dir)

    if sources_dir.exists():
        for entry in sources_dir.iterdir():
            if entry.is_symlink() and entry.name not in declared_aliases:
                entry.unlink()

    return status


def add_source(
    path: str,
    alias: str | None = None,
    fmt: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    sources_dir: Path = DEFAULT_SOURCES_DIR,
) -> dict:
    """`document-graph add <path>`の実体。alias自動生成・format自動推定・symlink同期・
    契約チェックまでを行い、結果を返す。"""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ConfigError(f"パスが見つかりません: {resolved}")

    config = load_config(config_path)
    existing_aliases = {s["alias"] for s in config["sources"]}

    for s in config["sources"]:
        if Path(s["path"]).resolve() == resolved:
            raise ConfigError(f"既に登録済みのソースです（alias={s['alias']}）: {resolved}")

    if alias:
        if alias in existing_aliases:
            raise ConfigError(f"alias '{alias}' は既に使われています")
        resolved_alias = alias
    else:
        resolved_alias = auto_alias(resolved, existing_aliases)

    resolved_fmt = fmt or detect_format(resolved)
    if resolved_fmt not in ("md", "html"):
        raise ConfigError("format は 'md' または 'html' を指定してください")

    config["sources"].append({"alias": resolved_alias, "path": str(resolved), "format": resolved_fmt})
    save_config(config, config_path)
    sync_status = sync_symlinks(config, sources_dir)

    # 契約チェック（frontmatter/meta未検出件数）は graph_index に委譲する。
    # config.py 自体は他モジュールへ依存しないよう、呼び出し側（cli.py）で行う。
    return {
        "alias": resolved_alias,
        "path": str(resolved),
        "format": resolved_fmt,
        "syncStatus": sync_status.get(resolved_alias, "unknown"),
    }


def remove_source(
    alias: str,
    config_path: Path = DEFAULT_CONFIG_PATH,
    sources_dir: Path = DEFAULT_SOURCES_DIR,
) -> bool:
    config = load_config(config_path)
    before = len(config["sources"])
    config["sources"] = [s for s in config["sources"] if s["alias"] != alias]
    if len(config["sources"]) == before:
        return False
    save_config(config, config_path)
    link = sources_dir / alias
    if link.is_symlink() or link.exists():
        link.unlink()
    return True

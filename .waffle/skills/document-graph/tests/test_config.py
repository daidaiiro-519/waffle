import json

import pytest

import config as config_mod


@pytest.fixture
def skill_env(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    return config_path, sources_dir


def test_load_config_missing_returns_empty_sources(skill_env):
    config_path, _ = skill_env
    assert config_mod.load_config(config_path) == {"sources": []}


def test_save_and_load_roundtrip(skill_env):
    config_path, _ = skill_env
    config_mod.save_config({"sources": [{"alias": "a", "path": "/tmp/a", "format": "md"}]}, config_path)
    loaded = config_mod.load_config(config_path)
    assert loaded["sources"][0]["alias"] == "a"


def test_auto_alias_generates_from_folder_name(tmp_path):
    folder = tmp_path / "my-docs"
    folder.mkdir()
    alias = config_mod.auto_alias(folder, existing=set())
    assert alias == "my-docs"


def test_auto_alias_resolves_collision_with_suffix(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    alias = config_mod.auto_alias(folder, existing={"docs", "docs-2"})
    assert alias == "docs-3"


def test_detect_format_majority_md(tmp_path):
    (tmp_path / "a.md").write_text("x")
    (tmp_path / "b.md").write_text("x")
    (tmp_path / "c.html").write_text("x")
    assert config_mod.detect_format(tmp_path) == "md"


def test_detect_format_majority_html(tmp_path):
    (tmp_path / "a.html").write_text("x")
    (tmp_path / "b.html").write_text("x")
    (tmp_path / "c.md").write_text("x")
    assert config_mod.detect_format(tmp_path) == "html"


def test_detect_format_single_file(tmp_path):
    f = tmp_path / "single.html"
    f.write_text("x")
    assert config_mod.detect_format(f) == "html"


def test_add_source_creates_config_and_symlink(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    target = tmp_path / "external-docs"
    target.mkdir()
    (target / "a.md").write_text("---\ntype: note\n---\nbody")

    result = config_mod.add_source(str(target), config_path=config_path, sources_dir=sources_dir)

    assert result["alias"] == "external-docs"
    assert result["format"] == "md"
    assert result["syncStatus"] == "created"
    link = sources_dir / "external-docs"
    assert link.is_symlink()
    assert link.resolve() == target.resolve()

    saved = json.loads(config_path.read_text())
    assert saved["sources"][0]["alias"] == "external-docs"


def test_add_source_duplicate_path_raises(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    target = tmp_path / "docs"
    target.mkdir()

    config_mod.add_source(str(target), config_path=config_path, sources_dir=sources_dir)
    with pytest.raises(config_mod.ConfigError):
        config_mod.add_source(str(target), config_path=config_path, sources_dir=sources_dir)


def test_add_source_missing_path_raises(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    with pytest.raises(config_mod.ConfigError):
        config_mod.add_source(str(tmp_path / "does-not-exist"), config_path=config_path, sources_dir=sources_dir)


def test_sync_symlinks_relinks_when_target_changes(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    target1 = tmp_path / "t1"
    target1.mkdir()
    target2 = tmp_path / "t2"
    target2.mkdir()

    config_mod.add_source(str(target1), alias="src", config_path=config_path, sources_dir=sources_dir)
    config = config_mod.load_config(config_path)
    config["sources"][0]["path"] = str(target2)
    config_mod.save_config(config, config_path)

    status = config_mod.sync_symlinks(config, sources_dir)
    assert status["src"] == "relinked"
    assert (sources_dir / "src").resolve() == target2.resolve()


def test_sync_symlinks_removes_stale_alias(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    target = tmp_path / "t1"
    target.mkdir()
    config_mod.add_source(str(target), alias="src", config_path=config_path, sources_dir=sources_dir)

    config_mod.remove_source("src", config_path=config_path, sources_dir=sources_dir)

    assert not (sources_dir / "src").exists()
    assert config_mod.list_sources(config_path) == []


def test_remove_source_unknown_alias_returns_false(tmp_path):
    config_path = tmp_path / "config.json"
    sources_dir = tmp_path / "sources"
    assert config_mod.remove_source("nope", config_path=config_path, sources_dir=sources_dir) is False

"""FsDocumentRepositoryのlink()に対するユニットテスト。"""
from waffle.adapters.outbound.fs import FsDocumentRepository


def test_linkはcanonicalへの相対シンボリックリンクを作る(tmp_path):
    canonical = tmp_path / "waffle" / "skills" / "x" / "SKILL.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("hello", encoding="utf-8")
    target = tmp_path / "claude" / "skills" / "x" / "SKILL.md"

    FsDocumentRepository().link(str(canonical), str(target))

    assert target.is_symlink()
    assert target.read_text(encoding="utf-8") == "hello"


def test_親ディレクトリがcanonical側への既存シンボリックリンクでも正本を壊さない(tmp_path):
    """
    Given deploy先の親ディレクトリが、canonicalの親ディレクトリへの
          既存シンボリックリンクである状態（旧来の手書きSkillのディレクトリ全体symlink）
    When linkを呼ぶ
    Then canonicalの内容は消えず、target経由でも読める（自己参照リンクにならない）
    """
    canonical_dir = tmp_path / "waffle" / "skills" / "x"
    canonical_dir.mkdir(parents=True)
    canonical = canonical_dir / "SKILL.md"
    canonical.write_text("hello", encoding="utf-8")

    claude_skills = tmp_path / "claude" / "skills"
    claude_skills.mkdir(parents=True)
    (claude_skills / "x").symlink_to(canonical_dir, target_is_directory=True)
    target = claude_skills / "x" / "SKILL.md"

    FsDocumentRepository().link(str(canonical), str(target))

    assert canonical.exists(), "canonicalが消えていないこと"
    assert canonical.read_text(encoding="utf-8") == "hello"
    assert target.read_text(encoding="utf-8") == "hello"

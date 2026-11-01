"""Unit tests for Git output parsing."""

from clankit.git.parser import (
    RECORD_SEP,
    UNIT_SEP,
    parse_branches,
    parse_diff,
    parse_log_nodes,
    parse_status_porcelain,
    parse_stashes,
    parse_tags,
)


def test_parse_status_porcelain_with_renames_and_upstream():
    raw = (
        "## main...origin/main [ahead 1, behind 2]\x00"
        " M file1.py\x00"
        "M  file2.py\x00"
        "?? untracked.txt\x00"
        "R  renamed_new.py\x00renamed_old.py\x00"
    )
    status = parse_status_porcelain(raw, root_dir="/repo")
    assert status.current_branch == "main"
    assert status.upstream == "origin/main"
    assert status.ahead == 1
    assert status.behind == 2
    assert len(status.files) == 4

    # file1.py
    assert status.files[0].path == "file1.py"
    assert status.files[0].is_unstaged is True
    assert status.files[0].is_staged is False

    # file2.py
    assert status.files[1].path == "file2.py"
    assert status.files[1].is_staged is True
    assert status.files[1].is_unstaged is False

    # untracked
    assert status.files[2].path == "untracked.txt"
    assert status.files[2].is_untracked is True

    # rename
    assert status.files[3].path == "renamed_new.py"
    assert status.files[3].orig_path == "renamed_old.py"
    assert status.files[3].index_status == "R"


def test_parse_status_initial_commit():
    raw = "## Initial commit on main\x00?? readme.md\x00"
    status = parse_status_porcelain(raw, root_dir="/repo")
    assert status.current_branch == "main"
    assert len(status.files) == 1
    assert status.files[0].path == "readme.md"


def test_parse_branches():
    raw = """* main                0123456 [origin/main: ahead 1] Commit subject 1
  dev                 abcdef0 [origin/dev: behind 3] Commit subject 2
  remotes/origin/main 0123456 Commit subject 1
"""
    branches = parse_branches(raw)
    assert len(branches) == 3

    assert branches[0].name == "main"
    assert branches[0].is_current is True
    assert branches[0].ahead == 1
    assert branches[0].behind == 0
    assert branches[0].commit_subject == "Commit subject 1"

    assert branches[1].name == "dev"
    assert branches[1].is_current is False
    assert branches[1].behind == 3

    assert branches[2].name == "origin/main"
    assert branches[2].is_remote is True
    assert branches[2].remote_name == "origin"
    assert branches[2].short_name == "main"


def test_parse_stashes():
    raw = """stash@{0}: WIP on main: c1d2e3f First stash
stash@{1}: On dev: a4b5c6d Second stash
"""
    stashes = parse_stashes(raw)
    assert len(stashes) == 2
    assert stashes[0].index == 0
    assert stashes[0].id == "stash@{0}"
    assert "First stash" in stashes[0].message
    assert stashes[1].index == 1


def test_parse_tags():
    raw = """v1.0.0
v1.1.0-rc1
"""
    tags = parse_tags(raw)
    assert len(tags) == 2
    assert tags[0].name == "v1.0.0"
    assert tags[1].name == "v1.1.0-rc1"


def test_parse_log_nodes():
    # Format: %x1e%H%x1f%h%x1f%P%x1f%an%x1f%ae%x1f%ad%x1f%d%x1f%s%x1f%b%x1e
    raw = (
        f"{RECORD_SEP}1111111111111111111111111111111111111111{UNIT_SEP}1111111{UNIT_SEP}2222222{UNIT_SEP}"
        f"Jane Doe{UNIT_SEP}jane@example.com{UNIT_SEP}2026-11-01 12:00:00{UNIT_SEP}"
        f"(HEAD -> main, origin/main, tag: v1.0){UNIT_SEP}Initial commit{UNIT_SEP}Extended body text{RECORD_SEP}"
    )
    commits = parse_log_nodes(raw)
    assert len(commits) == 1
    c = commits[0]
    assert c.hash == "1111111111111111111111111111111111111111"
    assert c.short_hash == "1111111"
    assert c.parents == ["2222222"]
    assert c.author_name == "Jane Doe"
    assert c.author_email == "jane@example.com"
    assert c.subject == "Initial commit"
    assert c.body == "Extended body text"
    assert "HEAD -> main" in c.refs
    assert "origin/main" in c.refs
    assert "tag: v1.0" in c.refs


def test_parse_diff():
    raw = """diff --git a/hello.py b/hello.py
index e69de29..496d649 100644
--- a/hello.py
+++ b/hello.py
@@ -1,3 +1,4 @@
 line 1
-old line 2
+new line 2
+added line 3
 line 4
"""
    diffs = parse_diff(raw)
    assert len(diffs) == 1
    fd = diffs[0]
    assert fd.old_path == "hello.py"
    assert fd.new_path == "hello.py"
    assert len(fd.hunks) == 1

    hunk = fd.hunks[0]
    assert hunk.old_start == 1
    assert hunk.old_count == 3
    assert hunk.new_start == 1
    assert hunk.new_count == 4

    types = [line.line_type for line in hunk.lines]
    assert "hunk_header" in types
    assert "deletion" in types
    assert "addition" in types
    assert "context" in types

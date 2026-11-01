"""Unit tests for Clankit Git models."""

from clankit.git.models import (
    BranchInfo,
    CommandResult,
    FileDelta,
    RepoStatus,
)


def test_command_result_display():
    res = CommandResult(
        command=["git", "commit", "-m", "hello world", "--author=Test <test@example.com>"],
        returncode=0,
        stdout="[main abc] hello world\n",
        stderr="",
        duration_ms=12.5,
        timestamp=1000.0,
        cwd="/tmp",
    )
    assert res.success is True
    assert res.display_command == 'git commit -m "hello world" "--author=Test <test@example.com>"'


def test_file_delta_properties():
    # Modified in worktree only
    d1 = FileDelta(path="file1.txt", index_status=" ", worktree_status="M")
    assert d1.is_staged is False
    assert d1.is_unstaged is True
    assert d1.is_untracked is False

    # Staged added only
    d2 = FileDelta(path="file2.txt", index_status="A", worktree_status=" ")
    assert d2.is_staged is True
    assert d2.is_unstaged is False

    # Staged modified AND worktree modified
    d3 = FileDelta(path="file3.txt", index_status="M", worktree_status="M")
    assert d3.is_staged is True
    assert d3.is_unstaged is True

    # Untracked
    d4 = FileDelta(path="file4.txt", index_status="?", worktree_status="?")
    assert d4.is_untracked is True
    assert d4.is_staged is False
    assert d4.is_unstaged is False

    # Conflict
    d5 = FileDelta(path="file5.txt", index_status="U", worktree_status="U")
    assert d5.is_conflict is True


def test_repo_status():
    status = RepoStatus(
        root_dir="/repo",
        current_branch="main",
        files=[
            FileDelta("staged.txt", index_status="A", worktree_status=" "),
            FileDelta("unstaged.txt", index_status=" ", worktree_status="M"),
            FileDelta("untracked.txt", index_status="?", worktree_status="?"),
        ],
    )
    assert not status.is_clean
    assert len(status.staged_files) == 1
    assert status.staged_files[0].path == "staged.txt"
    assert len(status.unstaged_files) == 2


def test_branch_info():
    b_local = BranchInfo(name="main", is_current=True)
    assert b_local.short_name == "main"

    b_remote = BranchInfo(
        name="origin/feature/login",
        is_remote=True,
        remote_name="origin",
    )
    assert b_remote.short_name == "feature/login"

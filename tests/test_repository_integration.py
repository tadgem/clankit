"""End-to-end integration tests using an isolated temporary Git repository."""

import os
import shutil
import subprocess
import tempfile
import pytest
from clankit.git.repository import GitRepository


@pytest.fixture
def temp_repo():
    tmp_dir = tempfile.mkdtemp(prefix="clankit_test_repo_")
    # Initialize real git repository
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_dir, check=True)

    # Initial commit
    file1 = os.path.join(tmp_dir, "file1.txt")
    with open(file1, "w") as f:
        f.write("Line 1\nLine 2\n")
    subprocess.run(["git", "add", "file1.txt"], cwd=tmp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_dir, check=True)

    repo = GitRepository(tmp_dir)
    yield repo, tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_integration_status_and_staging(temp_repo):
    repo, tmp_dir = temp_repo
    assert repo.is_valid() is True

    # 1. Modify file1.txt
    file1 = os.path.join(tmp_dir, "file1.txt")
    with open(file1, "a") as f:
        f.write("Line 3 modified\n")

    # 2. Add an untracked file
    file2 = os.path.join(tmp_dir, "untracked.py")
    with open(file2, "w") as f:
        f.write("print('hello')\n")

    status = repo.get_status()
    assert len(status.unstaged_files) == 2
    assert len(status.staged_files) == 0

    # 3. Stage file1.txt
    repo.stage_file("file1.txt")
    status = repo.get_status()
    assert len(status.staged_files) == 1
    assert status.staged_files[0].path == "file1.txt"

    # 4. Check diff
    diff_staged = repo.get_diff("file1.txt", staged=True)
    assert "+Line 3 modified" in diff_staged

    # 5. Unstage file1.txt
    repo.unstage_file("file1.txt")
    status = repo.get_status()
    assert len(status.staged_files) == 0
    assert len(status.unstaged_files) == 2


def test_integration_commit_and_branches(temp_repo):
    repo, tmp_dir = temp_repo

    # Stage all and commit
    file2 = os.path.join(tmp_dir, "feature.txt")
    with open(file2, "w") as f:
        f.write("feature code\n")

    repo.stage_all()
    res = repo.commit("Add feature", body="Detailed description of feature")
    assert res.success is True

    # Check commit log
    commits = repo.get_log(max_count=10)
    assert len(commits) == 2
    assert commits[0].subject == "Add feature"
    assert commits[0].body == "Detailed description of feature"

    # Create and checkout a branch
    res = repo.checkout_branch("feature/test-branch", create=True)
    assert res.success is True

    branches = repo.get_branches()
    branch_names = [b.name for b in branches]
    assert "feature/test-branch" in branch_names
    current = next(b for b in branches if b.is_current)
    assert current.name == "feature/test-branch"


def test_integration_stash(temp_repo):
    repo, tmp_dir = temp_repo

    file1 = os.path.join(tmp_dir, "file1.txt")
    with open(file1, "a") as f:
        f.write("Temporary uncommitted line\n")

    # Save stash
    res = repo.stash_save("WIP test stash")
    assert res.success is True

    stashes = repo.get_stashes()
    assert len(stashes) == 1
    assert "WIP test stash" in stashes[0].message

    # Pop stash
    res = repo.stash_pop()
    assert res.success is True

    stashes_after = repo.get_stashes()
    assert len(stashes_after) == 0

"""High-level Git repository facade wrapping standard Git CLI commands."""

from __future__ import annotations
import os
from typing import Callable, List, Optional, Tuple
from clankit.git.models import (
    BranchInfo,
    CommandResult,
    CommitNode,
    FileDiff,
    RepoStatus,
    StashInfo,
    TagInfo,
)
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
from clankit.git.runner import GitRunner


class GitRepository:
    """Manages a local Git repository strictly via standard Git CLI commands."""

    def __init__(self, path: str, runner: Optional[GitRunner] = None):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.runner = runner or GitRunner()
        self._root_path: Optional[str] = None

    @property
    def root(self) -> str:
        if self._root_path is None:
            detected = self.runner.find_repo_root(self.path)
            self._root_path = detected or self.path
        return self._root_path

    def is_valid(self) -> bool:
        """Check if target path is a valid git repository."""
        res = self.runner.run(["rev-parse", "--is-inside-work-tree"], cwd=self.path)
        return res.success and res.stdout.strip() == "true"

    def get_status(self) -> RepoStatus:
        """Fetch working tree and index status using standard porcelain v1."""
        res = self.runner.run(
            ["status", "--porcelain=v1", "-z", "-b", "-uall"],
            cwd=self.root,
        )
        return parse_status_porcelain(res.stdout, self.root)

    def get_branches(self) -> List[BranchInfo]:
        """Fetch list of all local and remote branches."""
        res = self.runner.run(["branch", "-a", "-vv", "--no-color"], cwd=self.root)
        return parse_branches(res.stdout)

    def get_stashes(self) -> List[StashInfo]:
        """Fetch list of all stashes."""
        res = self.runner.run(["stash", "list"], cwd=self.root)
        return parse_stashes(res.stdout)

    def get_tags(self) -> List[TagInfo]:
        """Fetch list of tags."""
        res = self.runner.run(["tag", "-l"], cwd=self.root)
        return parse_tags(res.stdout)

    def get_log(self, max_count: int = 300, revision: str = "--all") -> List[CommitNode]:
        """Fetch commit history with topological ordering for graph visualization."""
        fmt = f"{RECORD_SEP}%H{UNIT_SEP}%h{UNIT_SEP}%P{UNIT_SEP}%an{UNIT_SEP}%ae{UNIT_SEP}%ad{UNIT_SEP}%d{UNIT_SEP}%s{UNIT_SEP}%b{RECORD_SEP}"
        args = [
            "log",
            f"--max-count={max_count}",
            "--topo-order",
            f"--pretty=format:{fmt}",
            "--date=iso",
        ]
        if revision:
            args.append(revision)

        res = self.runner.run(args, cwd=self.root)
        return parse_log_nodes(res.stdout)

    def get_diff(self, file_path: Optional[str] = None, staged: bool = False) -> str:
        """Fetch unified diff for unstaged or staged changes."""
        args = ["diff", "--no-ext-diff", "-u"]
        if staged:
            args.append("--cached")
        if file_path:
            args.extend(["--", file_path])
        res = self.runner.run(args, cwd=self.root)
        return res.stdout

    def get_parsed_diff(self, file_path: Optional[str] = None, staged: bool = False) -> List[FileDiff]:
        """Fetch and parse unified diff."""
        raw = self.get_diff(file_path=file_path, staged=staged)
        return parse_diff(raw)

    def get_commit_diff(self, commit_hash: str, file_path: Optional[str] = None) -> str:
        """Fetch diff introduced by a specific commit."""
        args = ["show", "--no-ext-diff", "-u", commit_hash]
        if file_path:
            args.extend(["--", file_path])
        res = self.runner.run(args, cwd=self.root)
        return res.stdout

    def get_commit_files(self, commit_hash: str) -> List[Tuple[str, str]]:
        """Fetch list of changed files and their status in a specific commit."""
        res = self.runner.run(
            ["show", "--name-status", "--pretty=format:", commit_hash],
            cwd=self.root,
        )
        files = []
        for line in res.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                files.append((parts[0], parts[1]))
        return files

    # ---------------- Working copy operations ----------------

    def stage_file(self, path: str) -> CommandResult:
        """Stage a single file or directory."""
        return self.runner.run(["add", "--", path], cwd=self.root)

    def stage_all(self) -> CommandResult:
        """Stage all tracked and untracked changes."""
        return self.runner.run(["add", "-A"], cwd=self.root)

    def unstage_file(self, path: str) -> CommandResult:
        """Unstage a file from the index."""
        # Standard restore --staged with fallback to reset HEAD
        res = self.runner.run(["restore", "--staged", "--", path], cwd=self.root)
        if not res.success:
            res = self.runner.run(["reset", "HEAD", "--", path], cwd=self.root)
        return res

    def unstage_all(self) -> CommandResult:
        """Unstage all files."""
        res = self.runner.run(["restore", "--staged", "."], cwd=self.root)
        if not res.success:
            res = self.runner.run(["reset", "HEAD"], cwd=self.root)
        return res

    def discard_file(self, path: str, is_untracked: bool = False) -> CommandResult:
        """Discard changes to an unstaged file or remove untracked file."""
        if is_untracked:
            return self.runner.run(["clean", "-f", "-d", "--", path], cwd=self.root)
        return self.runner.run(["restore", "--", path], cwd=self.root)

    def commit(self, subject: str, body: str = "", amend: bool = False) -> CommandResult:
        """Commit staged changes."""
        args = ["commit"]
        if amend:
            args.append("--amend")
        args.extend(["-m", subject])
        if body.strip():
            args.extend(["-m", body.strip()])
        return self.runner.run(args, cwd=self.root)

    # ---------------- Branch & Remote operations ----------------

    def checkout_branch(self, branch_name: str, create: bool = False) -> CommandResult:
        """Checkout an existing or new branch."""
        if create:
            return self.runner.run(["checkout", "-b", branch_name], cwd=self.root)
        return self.runner.run(["checkout", branch_name], cwd=self.root)

    def delete_branch(self, branch_name: str, force: bool = False) -> CommandResult:
        """Delete a local branch."""
        flag = "-D" if force else "-d"
        return self.runner.run(["branch", flag, branch_name], cwd=self.root)

    def fetch_all(self, callback: Optional[Callable[[CommandResult], None]] = None) -> None:
        """Fetch from all remotes in background."""
        self.runner.run_async(["fetch", "--all", "--prune"], cwd=self.root, callback=callback)

    def pull(self, rebase: bool = False, callback: Optional[Callable[[CommandResult], None]] = None) -> None:
        """Pull from remote in background."""
        args = ["pull"]
        if rebase:
            args.append("--rebase")
        else:
            args.append("--ff-only")
        self.runner.run_async(args, cwd=self.root, callback=callback)

    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        set_upstream: bool = False,
        callback: Optional[Callable[[CommandResult], None]] = None,
    ) -> None:
        """Push commits to remote in background."""
        args = ["push"]
        if set_upstream:
            args.append("-u")
        args.append(remote)
        if branch:
            args.append(branch)
        self.runner.run_async(args, cwd=self.root, callback=callback)

    def merge(self, branch_name: str, no_ff: bool = True) -> CommandResult:
        """Merge a branch into the currently checked out branch."""
        args = ["merge"]
        if no_ff:
            args.append("--no-ff")
        args.append(branch_name)
        return self.runner.run(args, cwd=self.root)

    # ---------------- Stash operations ----------------

    def stash_save(self, message: str = "", keep_index: bool = False) -> CommandResult:
        """Stash current changes."""
        args = ["stash", "push", "-u"]
        if keep_index:
            args.append("--keep-index")
        if message:
            args.extend(["-m", message])
        return self.runner.run(args, cwd=self.root)

    def stash_pop(self, stash_id: str = "stash@{0}") -> CommandResult:
        """Pop a stash entry."""
        return self.runner.run(["stash", "pop", stash_id], cwd=self.root)

    def stash_drop(self, stash_id: str = "stash@{0}") -> CommandResult:
        """Drop a stash entry."""
        return self.runner.run(["stash", "drop", stash_id], cwd=self.root)

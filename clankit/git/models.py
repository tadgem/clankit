"""Data models for Clankit Git representation."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class FileStatusCode(str, Enum):
    INDEX_MODIFIED = "M"
    INDEX_ADDED = "A"
    INDEX_DELETED = "D"
    INDEX_RENAMED = "R"
    INDEX_COPIED = "C"
    UNMODIFIED = " "
    UNTRACKED = "?"
    IGNORED = "!"
    CONFLICT = "U"


@dataclass
class CommandResult:
    """Represents the execution outcome of a git CLI command."""
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timestamp: float
    cwd: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @property
    def display_command(self) -> str:
        # Quote arguments containing spaces
        formatted = []
        for arg in self.command:
            if " " in arg or '"' in arg or "'" in arg:
                formatted.append(f'"{arg}"')
            else:
                formatted.append(arg)
        return " ".join(formatted)


@dataclass
class FileDelta:
    """Represents a file change in the repository working tree or index."""
    path: str
    orig_path: Optional[str] = None
    index_status: str = " "
    worktree_status: str = " "

    @property
    def is_staged(self) -> bool:
        return self.index_status not in (" ", "?", "!")

    @property
    def is_unstaged(self) -> bool:
        return self.worktree_status not in (" ", "?", "!")

    @property
    def is_untracked(self) -> bool:
        return self.index_status == "?" and self.worktree_status == "?"

    @property
    def is_conflict(self) -> bool:
        return "U" in (self.index_status, self.worktree_status) or (
            self.index_status, self.worktree_status
        ) in [("A", "A"), ("D", "D")]

    @property
    def status_label(self) -> str:
        if self.is_conflict:
            return "Conflict"
        if self.is_untracked:
            return "Untracked"
        parts = []
        if self.is_staged:
            parts.append(f"Staged ({self.index_status})")
        if self.is_unstaged:
            parts.append(f"Modified ({self.worktree_status})")
        return ", ".join(parts) if parts else "Clean"


@dataclass
class BranchInfo:
    """Git branch details."""
    name: str
    is_current: bool = False
    is_remote: bool = False
    remote_name: Optional[str] = None
    tracking_branch: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    commit_hash: str = ""
    commit_subject: str = ""

    @property
    def short_name(self) -> str:
        if self.is_remote and self.remote_name and self.name.startswith(f"{self.remote_name}/"):
            return self.name[len(self.remote_name) + 1 :]
        return self.name


@dataclass
class StashInfo:
    """Git stash details."""
    index: int
    id: str  # e.g., stash@{0}
    message: str
    date: str = ""


@dataclass
class TagInfo:
    """Git tag details."""
    name: str
    commit_hash: str = ""
    message: str = ""


@dataclass
class DiffLine:
    """A single line within a diff hunk."""
    line_type: str  # 'addition', 'deletion', 'context', 'hunk_header', 'meta'
    content: str
    old_lineno: Optional[int] = None
    new_lineno: Optional[int] = None


@dataclass
class DiffHunk:
    """A hunk section within a diff."""
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    """Parsed unified diff for a single file."""
    old_path: str
    new_path: str
    is_binary: bool = False
    hunks: List[DiffHunk] = field(default_factory=list)
    raw: str = ""


@dataclass
class CommitNode:
    """Git commit representation with DAG visualization attributes."""
    hash: str
    short_hash: str
    parents: List[str]
    author_name: str
    author_email: str
    date: str
    subject: str
    body: str = ""
    refs: List[str] = field(default_factory=list)
    lane: int = 0
    # routes are (from_lane, to_lane, connection_type)
    routes: List[Tuple[int, int, str]] = field(default_factory=list)


@dataclass
class RepoStatus:
    """Overall status of the repository."""
    root_dir: str
    current_branch: Optional[str] = None
    is_detached: bool = False
    detached_head: str = ""
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    files: List[FileDelta] = field(default_factory=list)

    @property
    def staged_files(self) -> List[FileDelta]:
        return [f for f in self.files if f.is_staged]

    @property
    def unstaged_files(self) -> List[FileDelta]:
        return [f for f in self.files if f.is_unstaged or f.is_untracked]

    @property
    def is_clean(self) -> bool:
        return len(self.files) == 0

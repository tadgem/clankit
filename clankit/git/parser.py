"""Parsers for Git CLI command output."""

from __future__ import annotations
import re
from typing import List, Optional, Tuple
from clankit.git.models import (
    BranchInfo,
    CommitNode,
    DiffHunk,
    DiffLine,
    FileDelta,
    FileDiff,
    RepoStatus,
    StashInfo,
    TagInfo,
)


RECORD_SEP = "\x1e"
UNIT_SEP = "\x1f"


def parse_status_porcelain(raw_output: str, root_dir: str) -> RepoStatus:
    """Parse `git status --porcelain=v1 -z -b -uall` output."""
    status = RepoStatus(root_dir=root_dir)
    if not raw_output:
        return status

    # Entries are separated by NUL byte
    parts = raw_output.split("\x00")
    if not parts:
        return status

    # First entry is branch info starting with '## '
    branch_entry = parts[0]
    if branch_entry.startswith("## "):
        branch_line = branch_entry[3:].strip()
        _parse_branch_header(branch_line, status)

    i = 1
    total_parts = len(parts)
    while i < total_parts:
        entry = parts[i]
        if not entry:
            i += 1
            continue

        if len(entry) < 3:
            i += 1
            continue

        index_stat = entry[0]
        worktree_stat = entry[1]
        filepath = entry[3:]

        orig_path = None
        # In porcelain -z, a rename or copy has the source path as the immediately following NUL-separated token
        if index_stat in ("R", "C") or worktree_stat in ("R", "C"):
            if i + 1 < total_parts and parts[i + 1]:
                orig_path = parts[i + 1]
                i += 1

        delta = FileDelta(
            path=filepath,
            orig_path=orig_path,
            index_status=index_stat,
            worktree_status=worktree_stat,
        )
        status.files.append(delta)
        i += 1

    return status


def _parse_branch_header(line: str, status: RepoStatus) -> None:
    """Parse the `## ` header from git status."""
    if line.startswith("Initial commit on ") or line.startswith("No commits yet on "):
        branch = line.split(" on ")[-1].strip()
        status.current_branch = branch
        return

    if line.startswith("HEAD (no branch)") or "detached" in line:
        status.is_detached = True
        status.current_branch = "(detached HEAD)"
        # Try to extract commit if present
        m = re.search(r"HEAD \(no branch\)|detached at ([0-9a-f]+)", line)
        if m and m.group(1):
            status.detached_head = m.group(1)
        return

    # Syntax: <branch>...<upstream> [ahead X, behind Y]
    # or just: <branch>
    bracket_idx = line.find("[")
    ahead_behind_str = ""
    if bracket_idx != -1 and line.endswith("]"):
        ahead_behind_str = line[bracket_idx + 1 : -1]
        line = line[:bracket_idx].strip()

    if "..." in line:
        local_branch, upstream = line.split("...", 1)
        status.current_branch = local_branch.strip()
        status.upstream = upstream.strip()
    else:
        status.current_branch = line.strip()

    if ahead_behind_str:
        ahead_match = re.search(r"ahead (\d+)", ahead_behind_str)
        behind_match = re.search(r"behind (\d+)", ahead_behind_str)
        if ahead_match:
            status.ahead = int(ahead_match.group(1))
        if behind_match:
            status.behind = int(behind_match.group(1))


def parse_branches(raw_output: str) -> List[BranchInfo]:
    """Parse output of `git branch -a -vv --no-color`."""
    branches: List[BranchInfo] = []
    if not raw_output:
        return branches

    lines = raw_output.strip().splitlines()
    for line in lines:
        if not line.strip():
            continue

        is_current = line.startswith("* ")
        cleaned = line[2:].strip()

        # Format:
        # branch_name commit_sha [upstream: ahead X] commit_msg
        # or remotes/origin/main commit_sha commit_msg
        tokens = cleaned.split()
        if not tokens:
            continue

        branch_name = tokens[0]
        # Ignore HEAD symref like remotes/origin/HEAD -> origin/main
        if "->" in cleaned:
            continue

        is_remote = branch_name.startswith("remotes/")
        remote_name = None
        if is_remote:
            branch_name = branch_name[len("remotes/") :]
            if "/" in branch_name:
                remote_name = branch_name.split("/")[0]

        commit_hash = tokens[1] if len(tokens) > 1 else ""

        # Check for [upstream: ...]
        tracking_branch = None
        ahead = 0
        behind = 0
        m = re.search(r"\[([^\]]+)\]", cleaned)
        if m:
            bracket_content = m.group(1)
            parts = bracket_content.split(":")
            tracking_branch = parts[0].strip()
            if len(parts) > 1:
                ab_part = parts[1]
                am = re.search(r"ahead (\d+)", ab_part)
                bm = re.search(r"behind (\d+)", ab_part)
                if am:
                    ahead = int(am.group(1))
                if bm:
                    behind = int(bm.group(1))

        # Remainder is commit subject
        subject = ""
        # Find position after hash and bracket
        last_meta_idx = cleaned.find("]")
        if last_meta_idx != -1:
            subject = cleaned[last_meta_idx + 1 :].strip()
        elif len(tokens) > 2:
            subject = " ".join(tokens[2:])

        branches.append(
            BranchInfo(
                name=branch_name,
                is_current=is_current,
                is_remote=is_remote,
                remote_name=remote_name,
                tracking_branch=tracking_branch,
                ahead=ahead,
                behind=behind,
                commit_hash=commit_hash,
                commit_subject=subject,
            )
        )

    return branches


def parse_stashes(raw_output: str) -> List[StashInfo]:
    """Parse `git stash list`."""
    stashes: List[StashInfo] = []
    if not raw_output:
        return stashes

    for idx, line in enumerate(raw_output.strip().splitlines()):
        if not line.strip():
            continue
        # e.g.: stash@{0}: WIP on main: c1d2e3f Subject...
        m = re.match(r"(stash@\{(\d+)\}):\s*(.*)", line)
        if m:
            stash_id = m.group(1)
            index = int(m.group(2))
            message = m.group(3)
            stashes.append(StashInfo(index=index, id=stash_id, message=message))
        elif ":" in line:
            parts = line.split(":", 1)
            stashes.append(StashInfo(index=idx, id=f"stash@{{{idx}}}", message=parts[1].strip()))
    return stashes


def parse_tags(raw_output: str) -> List[TagInfo]:
    """Parse `git tag -l`."""
    tags: List[TagInfo] = []
    if not raw_output:
        return tags

    for line in raw_output.strip().splitlines():
        name = line.strip()
        if name:
            tags.append(TagInfo(name=name))
    return tags


def parse_log_nodes(raw_output: str) -> List[CommitNode]:
    """Parse git log output formatted with ASCII unit and record separators.

    Format string: %x1e%H%x1f%h%x1f%P%x1f%an%x1f%ae%x1f%ad%x1f%d%x1f%s%x1f%b%x1e
    """
    commits: List[CommitNode] = []
    if not raw_output:
        return commits

    records = raw_output.split(RECORD_SEP)
    for record in records:
        record = record.strip()
        if not record:
            continue

        fields = record.split(UNIT_SEP)
        if len(fields) < 8:
            continue

        full_hash = fields[0].strip()
        short_hash = fields[1].strip()
        parents_str = fields[2].strip()
        author_name = fields[3].strip()
        author_email = fields[4].strip()
        date_str = fields[5].strip()
        ref_decorations = fields[6].strip()
        subject = fields[7].strip()
        body = fields[8].strip() if len(fields) > 8 else ""

        parents = parents_str.split() if parents_str else []

        # Parse ref decorations like: (HEAD -> main, origin/main, tag: v1.0)
        refs = []
        if ref_decorations:
            decorations = ref_decorations.strip("() ")
            for item in decorations.split(","):
                item_clean = item.strip()
                if item_clean:
                    refs.append(item_clean)

        commits.append(
            CommitNode(
                hash=full_hash,
                short_hash=short_hash,
                parents=parents,
                author_name=author_name,
                author_email=author_email,
                date=date_str,
                subject=subject,
                body=body,
                refs=refs,
            )
        )

    return commits


def parse_diff(raw_diff: str) -> List[FileDiff]:
    """Parse raw git diff output into FileDiff objects with hunks and lines."""
    file_diffs: List[FileDiff] = []
    if not raw_diff:
        return file_diffs

    current_file: Optional[FileDiff] = None
    current_hunk: Optional[DiffHunk] = None
    old_line_counter = 0
    new_line_counter = 0

    lines = raw_diff.splitlines()
    for line in lines:
        if line.startswith("diff --git "):
            # Start of a new file diff
            if current_hunk and current_file:
                current_file.hunks.append(current_hunk)
                current_hunk = None
            if current_file:
                file_diffs.append(current_file)

            # Extract old and new file paths: diff --git a/path b/path
            m = re.match(r"diff --git a/(.*) b/(.*)", line)
            if m:
                current_file = FileDiff(old_path=m.group(1), new_path=m.group(2), raw=line + "\n")
            else:
                current_file = FileDiff(old_path="", new_path="", raw=line + "\n")
            continue

        if current_file is None:
            continue

        current_file.raw += line + "\n"

        if line.startswith("Binary files "):
            current_file.is_binary = True
            continue

        # Check for hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@ "):
            if current_hunk:
                current_file.hunks.append(current_hunk)

            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)", line)
            if m:
                old_start = int(m.group(1))
                old_count = int(m.group(2)) if m.group(2) else 1
                new_start = int(m.group(3))
                new_count = int(m.group(4)) if m.group(4) else 1
                current_hunk = DiffHunk(
                    header=line,
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    lines=[],
                )
                current_hunk.lines.append(DiffLine(line_type="hunk_header", content=line))
                old_line_counter = old_start
                new_line_counter = new_start
            continue

        if current_hunk is None:
            # Metadata header line (index, ---, +++, mode, etc.)
            continue

        if line.startswith("+"):
            current_hunk.lines.append(
                DiffLine(
                    line_type="addition",
                    content=line,
                    old_lineno=None,
                    new_lineno=new_line_counter,
                )
            )
            new_line_counter += 1
        elif line.startswith("-"):
            current_hunk.lines.append(
                DiffLine(
                    line_type="deletion",
                    content=line,
                    old_lineno=old_line_counter,
                    new_lineno=None,
                )
            )
            old_line_counter += 1
        elif line.startswith(" ") or not line:
            current_hunk.lines.append(
                DiffLine(
                    line_type="context",
                    content=line,
                    old_lineno=old_line_counter,
                    new_lineno=new_line_counter,
                )
            )
            old_line_counter += 1
            new_line_counter += 1
        elif line.startswith("\\ No newline at end of file"):
            current_hunk.lines.append(DiffLine(line_type="meta", content=line))

    if current_hunk and current_file:
        current_file.hunks.append(current_hunk)
    if current_file:
        file_diffs.append(current_file)

    return file_diffs

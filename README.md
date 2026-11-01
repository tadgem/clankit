# Clankit

A fast, lightweight, and responsive Git GUI wrapper written in Python that looks and functions like **Atlassian SourceTree**, powered by **Dear PyGui** (the modern Dear ImGui Python framework).

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Framework DearPyGui](https://img.shields.io/badge/GUI-Dear%20PyGui%20(Dear%20ImGui)-purple.svg)
![Credential Unbiased](https://img.shields.io/badge/Credentials-Native%20Git%20CLI-success.svg)

---

## Key Features

1. **SourceTree-Inspired Layout & Workflow**:
   - **Top Toolbar**: Immediate access to `Commit`, `Pull`, `Push`, `Fetch`, `Branch`, `Merge`, `Stash`, `Discard`, `Terminal`, `Theme` switcher, and `Refresh` with ahead/behind badges (`⇡1 ⇣2`).
   - **Active Operation Progress**: Visual animated rotating progress spinner and status indicator when network operations (`push`, `pull`, `fetch`) are executing.
   - **Modern Typography**: High-resolution Open Sans UI font with crisp anti-aliasing and DejaVu Sans Mono code font for diff inspection and terminal logs.
   - **Multi-Theme Support**: Built-in themes with live real-time switching and preference persistence:
     - `SourceTree Dark` (Classic dark theme)
     - `SourceTree Light` (Modern clean light theme)
     - `GitHub Dark` (Modern GitHub dark palette)
     - `Nord` (Arctic north-bluish palette)
     - `Solarized Dark` (Classic low-contrast programmer palette)
   - **Left Navigation Sidebar**:
     - **Workspace**: Quick toggle between `File Status` (uncommitted changes) and `History` (commit graph).
     - **Branches**: Local branches with active checkout indicators; right-click / quick actions to checkout or delete.
     - **Remotes**: Grouped by remote (`origin`, etc.) listing all remote-tracking branches.
     - **Stashes**: Instant view of stashes with single-click `Pop` or `Drop`.
     - **Tags**: Visual list of tags.
   - **Working Tree & Staging View**:
     - Split tables for **Unstaged Files** and **Staged Files** with file status letters (`[M]`, `[A]`, `[D]`, `[?]`, `[U]`).
     - Action buttons: `Stage All`, `Unstage All`, `Stage`, `Unstage`, and `Discard`.
     - Integrated multi-line **Commit Composer** supporting commit summary, extended description, amending last commit, and pushing immediately.
   - **Interactive Diff Viewer**:
     - Unified diff renderer with syntax highlighting: green additions (`+`), red deletions (`-`), cyan hunk headers (`@@`), and gray metadata.
   - **History View & Visual Commit DAG**:
     - Topological commit graph with branch track lanes and visual node indicators (`●`).
     - Badges for `HEAD -> main`, `origin/main`, tags, and branch pointers.
     - Filter/search bar to filter commits in real-time by message, author, or SHA.
     - Detailed commit inspector showing author, date, parent SHAs, commit message, list of changed files, and individual file diffs.
   - **Git Activity Console**:
     - A collapsible drawer at the bottom displaying every exact Git CLI command executed in real time, with execution duration in ms, return code, and full stdout/stderr output.

2. **Strictly Credential-Unbiased**:
   - Clankit does not store, intercept, or invent custom credential mechanisms.
   - All operations are dispatched directly to the host system's standard `git` CLI, inheriting all environment variables (`SSH_AUTH_SOCK`, `GIT_SSH_COMMAND`, `HOME`, etc.).
   - Works natively with your existing SSH keys, GPG signing, and standard credential helpers (`git-credential-manager`, `libsecret`, `osxkeychain`, `store`, `cache`).

3. **High Performance**:
   - Built on Dear PyGui (Dear ImGui C++ engine), rendering at 60 FPS with immediate visual response.
   - Long-running network commands (`fetch`, `pull`, `push`) run asynchronously in background thread pools, keeping the UI fluid and interactive.

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Linux)
- `git` installed on your system PATH
- OpenGL-capable display server (X11 or Wayland)

### Quick Start

```bash
# 1. Clone or navigate to the repository
cd /path/to/clankit

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install clankit
pip install -e .

# 4. Launch Clankit in the current directory or specify a target repo
clankit
# or specify a path:
clankit /path/to/another/repo
```

### Desktop Application Installation

You can install Clankit so that it shows up in your desktop application launcher (GNOME, KDE Plasma, XFCE, Rofi, etc.) with custom application icons:

```bash
# Install to your user environment:
pip install .

# Register the application in your system application menu:
clankit --install-desktop
```

To uninstall desktop integration at any time:
```bash
clankit --uninstall-desktop
```

### CLI Options

```text
usage: clankit [-h] [--version] [--install-desktop] [--uninstall-desktop] [--theme THEME] [path]

positional arguments:
  path                 Path to the Git repository (default: current directory)

options:
  -h, --help           show this help message and exit
  --version            Show Clankit version and exit
  --install-desktop    Install desktop launcher (.desktop) and application icons
  --uninstall-desktop  Uninstall system desktop launcher and application icons
  --theme THEME        Initial theme to use ('SourceTree Dark', 'SourceTree Light', 'GitHub Dark', 'Nord', 'Solarized Dark')
```

---

## Git CLI Command Mapping

Every user action maps transparently to standard Git CLI commands:

| GUI Action | Executed Git Command | Notes |
| :--- | :--- | :--- |
| **Status Check** | `git status --porcelain=v1 -z -b -uall` | Machine-readable, zero quoting ambiguity |
| **Stage File** | `git add -- <path>` | Staging index |
| **Stage All** | `git add -A` | Stage all working tree modifications & untracked |
| **Unstage File**| `git restore --staged -- <path>` | Index reset |
| **Unstage All** | `git restore --staged .` | Reset all staged changes |
| **Discard File**| `git restore -- <path>` / `git clean -f -d -- <path>` | Reverts working tree or deletes untracked |
| **Commit** | `git commit -m "<subject>" -m "<body>"` | Standard commit |
| **Amend** | `git commit --amend -m "<subject>" -m "<body>"` | Amend HEAD commit |
| **Checkout** | `git checkout <branch>` | Switch branch |
| **New Branch** | `git checkout -b <new_branch>` | Create and switch branch |
| **Merge** | `git merge --no-ff <branch>` | Create merge commit |
| **Fetch** | `git fetch --all --prune` | Background thread |
| **Pull** | `git pull --ff-only` | Background thread |
| **Push** | `git push origin <branch>` | Background thread |
| **Stash Save** | `git stash push -u -m "<message>"` | Save working copy changes |
| **Stash Pop** | `git stash pop <stash_id>` | Restore stash |
| **Log History** | `git log --max-count=250 --topo-order --pretty=format:... --all` | Topological commit DAG |
| **Diff** | `git diff --no-ext-diff -u -- <path>` | Unified diff |

---

## Running the Test Suite

```bash
.venv/bin/pytest -v
```

The test suite covers:
- Subprocess execution, environment preservation, and error handling.
- Git porcelain status, branch, stash, tag, and diff parsers.
- Commit DAG graph layout and lane routing algorithms.
- Full end-to-end integration tests using an isolated temporary Git repository.
- Dear PyGui lifecycle and frame rendering smoke test.

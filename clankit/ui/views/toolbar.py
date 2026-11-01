"""Top action toolbar matching SourceTree layout and functionality."""

from __future__ import annotations
import os
import subprocess
from typing import Callable, Optional
import dearpygui.dearpygui as dpg
from clankit.git.models import RepoStatus
from clankit.ui.theme import SourceTreeColors, create_primary_button_theme


class ToolbarComponent:
    """Renders the top action toolbar."""

    def __init__(
        self,
        parent_tag: str,
        on_open_repo: Callable[[], None],
        on_refresh: Callable[[], None],
        on_commit_click: Callable[[], None],
        on_pull_click: Callable[[], None],
        on_push_click: Callable[[], None],
        on_fetch_click: Callable[[], None],
        on_branch_click: Callable[[], None],
        on_merge_click: Callable[[], None],
        on_stash_click: Callable[[], None],
        on_discard_click: Callable[[], None],
        get_repo_path: Callable[[], str],
    ):
        self.parent_tag = parent_tag
        self.on_open_repo = on_open_repo
        self.on_refresh = on_refresh
        self.on_commit_click = on_commit_click
        self.on_pull_click = on_pull_click
        self.on_push_click = on_push_click
        self.on_fetch_click = on_fetch_click
        self.on_branch_click = on_branch_click
        self.on_merge_click = on_merge_click
        self.on_stash_click = on_stash_click
        self.on_discard_click = on_discard_click
        self.get_repo_path = get_repo_path

        self.pull_btn_tag = "tb_pull_btn"
        self.push_btn_tag = "tb_push_btn"
        self.status_text_tag = "tb_status_text"
        self.repo_text_tag = "tb_repo_text"

    def build(self) -> None:
        """Construct toolbar items."""
        with dpg.group(parent=self.parent_tag, horizontal=True):
            dpg.add_button(label="Open Repo", callback=self.on_open_repo)
            dpg.add_button(label="Refresh", callback=self.on_refresh)

            dpg.add_text(" | ", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_button(label="Commit", callback=self.on_commit_click)
            dpg.add_button(label="Pull", tag=self.pull_btn_tag, callback=self.on_pull_click)
            dpg.add_button(label="Push", tag=self.push_btn_tag, callback=self.on_push_click)
            dpg.add_button(label="Fetch", callback=self.on_fetch_click)

            dpg.add_text(" | ", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_button(label="Branch", callback=self.on_branch_click)
            dpg.add_button(label="Merge", callback=self.on_merge_click)
            dpg.add_button(label="Stash", callback=self.on_stash_click)
            dpg.add_button(label="Discard", callback=self.on_discard_click)
            dpg.add_button(label="Terminal", callback=self._launch_terminal)

        dpg.add_spacer(height=3)

        # Status info line
        with dpg.group(parent=self.parent_tag, horizontal=True):
            dpg.add_text("Repo: ", color=SourceTreeColors.TEXT_MUTED)
            dpg.add_text(self.get_repo_path(), tag=self.repo_text_tag, color=SourceTreeColors.PRIMARY_BLUE)
            dpg.add_text("  Branch: ", color=SourceTreeColors.TEXT_MUTED)
            dpg.add_text("loading...", tag=self.status_text_tag, color=SourceTreeColors.STATUS_ADDED)

    def update_status(self, status: RepoStatus) -> None:
        """Update toolbar indicators based on repository status."""
        dpg.set_value(self.repo_text_tag, status.root_dir)

        # Update pull/push labels with ahead/behind badges
        pull_label = f"Pull ({status.behind})" if status.behind > 0 else "Pull"
        push_label = f"Push ({status.ahead})" if status.ahead > 0 else "Push"
        dpg.configure_item(self.pull_btn_tag, label=pull_label)
        dpg.configure_item(self.push_btn_tag, label=push_label)

        branch_name = status.current_branch or "None"
        badges = []
        if status.ahead > 0:
            badges.append(f"⇡{status.ahead}")
        if status.behind > 0:
            badges.append(f"⇣{status.behind}")

        badge_str = f" ({' '.join(badges)})" if badges else ""
        dpg.set_value(self.status_text_tag, f"{branch_name}{badge_str}")

    def _launch_terminal(self) -> None:
        """Launch user terminal in repository directory."""
        cwd = self.get_repo_path()
        terminals = [
            os.environ.get("TERMINAL"),
            "kitty",
            "alacritty",
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "xterm",
        ]
        for term in terminals:
            if not term:
                continue
            try:
                subprocess.Popen([term], cwd=cwd)
                return
            except FileNotFoundError:
                continue

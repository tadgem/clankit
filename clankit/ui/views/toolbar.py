"""Top action toolbar matching SourceTree layout and functionality."""

from __future__ import annotations
import os
import subprocess
from typing import Callable, Optional
import dearpygui.dearpygui as dpg
from clankit.git.models import RepoStatus
from clankit.ui.theme import SourceTreeColors, get_theme_manager


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
        on_theme_change: Optional[Callable[[str], None]] = None,
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
        self.on_theme_change = on_theme_change

        self.pull_btn_tag = "tb_pull_btn"
        self.push_btn_tag = "tb_push_btn"
        self.fetch_btn_tag = "tb_fetch_btn"
        self.status_text_tag = "tb_status_text"
        self.repo_text_tag = "tb_repo_text"

        self.progress_group_tag = "tb_progress_group"
        self.progress_spinner_tag = "tb_progress_spinner"
        self.progress_text_tag = "tb_progress_text"
        self.theme_combo_tag = "tb_theme_combo"

    def build(self) -> None:
        """Construct toolbar items."""
        theme_mgr = get_theme_manager()
        current_display = theme_mgr.current_theme.display_name
        theme_names = theme_mgr.get_display_names()

        # Top Button Actions Row
        with dpg.group(parent=self.parent_tag, horizontal=True):
            dpg.add_button(label="Open Repo", callback=self.on_open_repo)
            dpg.add_button(label="Refresh", callback=self.on_refresh)

            dpg.add_text(" | ", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_button(label="Commit", callback=self.on_commit_click)
            dpg.add_button(label="Pull", tag=self.pull_btn_tag, callback=self.on_pull_click)
            dpg.add_button(label="Push", tag=self.push_btn_tag, callback=self.on_push_click)
            dpg.add_button(label="Fetch", tag=self.fetch_btn_tag, callback=self.on_fetch_click)

            dpg.add_text(" | ", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_button(label="Branch", callback=self.on_branch_click)
            dpg.add_button(label="Merge", callback=self.on_merge_click)
            dpg.add_button(label="Stash", callback=self.on_stash_click)
            dpg.add_button(label="Discard", callback=self.on_discard_click)
            dpg.add_button(label="Terminal", callback=self._launch_terminal)

            dpg.add_text(" | ", color=SourceTreeColors.TEXT_MUTED)

            # Theme Switcher Selector
            dpg.add_text("Theme:")
            dpg.add_combo(
                items=theme_names,
                default_value=current_display,
                tag=self.theme_combo_tag,
                width=150,
                callback=self._handle_theme_change,
            )

        dpg.add_spacer(height=3, parent=self.parent_tag)

        # Status Info & Active Background Progress Indicator Row
        with dpg.group(parent=self.parent_tag, horizontal=True):
            dpg.add_text("Repo: ", color=SourceTreeColors.TEXT_MUTED)
            dpg.add_text(self.get_repo_path(), tag=self.repo_text_tag, color=SourceTreeColors.PRIMARY_BLUE)
            dpg.add_text("   Branch: ", color=SourceTreeColors.TEXT_MUTED)
            dpg.add_text("loading...", tag=self.status_text_tag, color=SourceTreeColors.STATUS_ADDED)

            # Active network operation progress group (hidden when idle)
            with dpg.group(tag=self.progress_group_tag, horizontal=True, show=False):
                dpg.add_text("   |   ", color=SourceTreeColors.TEXT_MUTED)
                dpg.add_loading_indicator(
                    tag=self.progress_spinner_tag,
                    style=dpg.mvLoadInd_Ring,
                    radius=1.8,
                    thickness=1.5,
                    color=SourceTreeColors.PRIMARY_BLUE,
                )
                dpg.add_text("", tag=self.progress_text_tag, color=SourceTreeColors.PRIMARY_BLUE)

    def _handle_theme_change(self, sender: str | int, app_data: str) -> None:
        if self.on_theme_change and app_data:
            self.on_theme_change(app_data)

    def set_busy(self, busy: bool, message: str = "") -> None:
        """Toggle network operation progress indicator and button states."""
        if not dpg.does_item_exist(self.progress_group_tag):
            return

        if busy:
            dpg.configure_item(self.pull_btn_tag, enabled=False)
            dpg.configure_item(self.push_btn_tag, enabled=False)
            dpg.configure_item(self.fetch_btn_tag, enabled=False)
            dpg.set_value(self.progress_text_tag, message)
            dpg.show_item(self.progress_group_tag)
        else:
            dpg.configure_item(self.pull_btn_tag, enabled=True)
            dpg.configure_item(self.push_btn_tag, enabled=True)
            dpg.configure_item(self.fetch_btn_tag, enabled=True)
            dpg.hide_item(self.progress_group_tag)

    def update_status(self, status: RepoStatus) -> None:
        """Update toolbar indicators based on repository status."""
        if dpg.does_item_exist(self.repo_text_tag):
            dpg.set_value(self.repo_text_tag, status.root_dir)

        # Update pull/push labels with ahead/behind badges
        pull_label = f"Pull ({status.behind})" if status.behind > 0 else "Pull"
        push_label = f"Push ({status.ahead})" if status.ahead > 0 else "Push"
        if dpg.does_item_exist(self.pull_btn_tag):
            dpg.configure_item(self.pull_btn_tag, label=pull_label)
        if dpg.does_item_exist(self.push_btn_tag):
            dpg.configure_item(self.push_btn_tag, label=push_label)

        branch_name = status.current_branch or "None"
        badges = []
        if status.ahead > 0:
            badges.append(f"⇡{status.ahead}")
        if status.behind > 0:
            badges.append(f"⇣{status.behind}")

        badge_str = f" ({' '.join(badges)})" if badges else ""
        if dpg.does_item_exist(self.status_text_tag):
            dpg.set_value(self.status_text_tag, f"{branch_name}{badge_str}")

    def update_theme(self) -> None:
        """Update toolbar colored widgets to match current theme."""
        if dpg.does_item_exist(self.repo_text_tag):
            dpg.configure_item(self.repo_text_tag, color=SourceTreeColors.PRIMARY_BLUE)
        if dpg.does_item_exist(self.status_text_tag):
            dpg.configure_item(self.status_text_tag, color=SourceTreeColors.STATUS_ADDED)
        if dpg.does_item_exist(self.progress_spinner_tag):
            dpg.configure_item(self.progress_spinner_tag, color=SourceTreeColors.PRIMARY_BLUE)
        if dpg.does_item_exist(self.progress_text_tag):
            dpg.configure_item(self.progress_text_tag, color=SourceTreeColors.PRIMARY_BLUE)

        theme_mgr = get_theme_manager()
        if dpg.does_item_exist(self.theme_combo_tag):
            dpg.set_value(self.theme_combo_tag, theme_mgr.current_theme.display_name)

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

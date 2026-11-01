"""Main application controller for Clankit."""

from __future__ import annotations
import os
import queue
import threading
from typing import Optional
import dearpygui.dearpygui as dpg

from clankit.desktop import get_asset_path
from clankit.git.models import CommandResult, FileDelta, RepoStatus
from clankit.git.repository import GitRepository
from clankit.git.runner import GitRunner
from clankit.ui.font_manager import FontManager
from clankit.ui.theme import apply_sourcetree_theme, get_theme_manager
from clankit.ui.views.console_view import ConsoleViewComponent
from clankit.ui.views.dialogs import DialogManager
from clankit.ui.views.history_view import HistoryViewComponent
from clankit.ui.views.sidebar import SidebarComponent
from clankit.ui.views.staging_view import StagingViewComponent
from clankit.ui.views.toolbar import ToolbarComponent


class ClankitApp:
    """Clankit main application window and event coordinator."""

    def __init__(self, initial_path: Optional[str] = None):
        self.initial_path = initial_path or os.getcwd()
        self.runner = GitRunner()
        self.repo = GitRepository(self.initial_path, runner=self.runner)

        self.dialogs = DialogManager()
        self.font_manager = FontManager()
        self.theme_manager = get_theme_manager()
        self.toolbar: Optional[ToolbarComponent] = None
        self.sidebar: Optional[SidebarComponent] = None
        self.staging_view: Optional[StagingViewComponent] = None
        self.history_view: Optional[HistoryViewComponent] = None
        self.console_view: Optional[ConsoleViewComponent] = None

        self.current_view: str = "status"  # 'status' or 'history'
        self._action_queue: queue.Queue = queue.Queue()

        # Connect command runner listener
        self.runner.add_listener(self._on_command_executed)

    def _on_command_executed(self, result: CommandResult) -> None:
        """Called whenever a git CLI command finishes."""
        # Queue console update to ensure thread safety
        self._action_queue.put(("log_cmd", result))

    def build_ui(self) -> None:
        """Construct the full Dear PyGui layout."""
        dpg.create_context()
        self.font_manager.setup_fonts(ui_size=15, mono_size=14)
        apply_sourcetree_theme()

        with dpg.window(tag="main_window", label="Clankit", no_title_bar=True):
            # 1. Top Toolbar
            toolbar_container = dpg.add_group(tag="toolbar_container")
            self.toolbar = ToolbarComponent(
                parent_tag=toolbar_container,
                on_open_repo=self._action_open_repo_dialog,
                on_refresh=self.refresh,
                on_commit_click=self._action_nav_commit,
                on_pull_click=self._action_pull,
                on_push_click=self._action_push,
                on_fetch_click=self._action_fetch,
                on_branch_click=self._action_branch_dialog,
                on_merge_click=self._action_merge_dialog,
                on_stash_click=self._action_stash_dialog,
                on_discard_click=self._action_discard_unstaged_dialog,
                get_repo_path=lambda: self.repo.root,
                on_theme_change=self._action_change_theme,
            )
            self.toolbar.build()

            dpg.add_separator()
            dpg.add_spacer(height=2)

            # 2. Main Middle Area (Sidebar + Content View)
            middle_group = dpg.add_group(horizontal=True, tag="middle_group")

            # Left Sidebar
            self.sidebar = SidebarComponent(
                parent_tag=middle_group,
                on_select_view=self._switch_view,
                on_checkout_branch=self._action_checkout_branch,
                on_delete_branch=self._action_delete_branch,
                on_pop_stash=self._action_pop_stash,
                on_drop_stash=self._action_drop_stash,
            )
            self.sidebar.build()

            # Right Content Container
            content_container = dpg.add_child_window(parent=middle_group, tag="content_container", border=False)

            self.staging_view = StagingViewComponent(
                parent_tag=content_container,
                on_stage_file=self._action_stage_file,
                on_stage_all=self._action_stage_all,
                on_unstage_file=self._action_unstage_file,
                on_unstage_all=self._action_unstage_all,
                on_discard_file=self._action_discard_single_file_dialog,
                on_commit=self._action_commit,
                on_request_diff=self._handle_request_diff,
            )
            self.staging_view.build()

            self.history_view = HistoryViewComponent(
                parent_tag=content_container,
                on_request_commit_diff=self._handle_request_commit_diff,
                on_request_commit_files=self._handle_request_commit_files,
            )
            self.history_view.build()

            # Monospace font binding for code diffs
            if hasattr(self.staging_view, "diff_viewer"):
                self.font_manager.bind_mono_font(self.staging_view.diff_viewer.tag)
            if hasattr(self.history_view, "diff_viewer"):
                self.font_manager.bind_mono_font(self.history_view.diff_viewer.tag)

            # 3. Bottom Git Activity Console Drawer
            dpg.add_spacer(height=2)
            self.console_view = ConsoleViewComponent(parent_tag="main_window")
            self.console_view.build()
            if hasattr(self.console_view, "output_text_tag"):
                self.font_manager.bind_mono_font(self.console_view.output_text_tag)

        dpg.create_viewport(
            title=f"Clankit - {os.path.basename(self.repo.root)}",
            width=1280,
            height=820,
            min_width=960,
            min_height=600,
        )

        # Set application window and taskbar icons
        icon_small = get_asset_path("icons/clankit_32.png")
        icon_large = get_asset_path("icons/clankit_256.png")
        if os.path.exists(icon_small):
            try:
                dpg.set_viewport_small_icon(icon_small)
            except Exception:
                pass
        if os.path.exists(icon_large):
            try:
                dpg.set_viewport_large_icon(icon_large)
            except Exception:
                pass

        dpg.setup_dearpygui()
        dpg.set_primary_window("main_window", True)

    def _switch_view(self, view_name: str) -> None:
        self.current_view = view_name
        if view_name == "status":
            dpg.show_item(self.staging_view.tag)
            dpg.hide_item(self.history_view.tag)
        else:
            dpg.hide_item(self.staging_view.tag)
            dpg.show_item(self.history_view.tag)

    def open_repository(self, path: str) -> None:
        """Switch to another repository."""
        expanded_path = os.path.abspath(os.path.expanduser(path))
        new_repo = GitRepository(expanded_path, runner=self.runner)
        if not new_repo.is_valid():
            self.dialogs.show_error("Invalid Repository", f"The directory '{path}' is not a valid Git repository.")
            return

        self.repo = new_repo
        dpg.set_viewport_title(f"Clankit - {os.path.basename(self.repo.root)}")

        # Reset views before loading new repository data
        if self.history_view:
            self.history_view.reset()
        if self.staging_view:
            self.staging_view.reset()

        self.refresh()

    def refresh(self) -> None:
        """Reload all repository data from Git CLI."""
        if not self.repo.is_valid():
            return

        status = self.repo.get_status()
        branches = self.repo.get_branches()
        stashes = self.repo.get_stashes()
        tags = self.repo.get_tags()
        commits = self.repo.get_log(max_count=250)

        # Update Toolbar
        if self.toolbar:
            self.toolbar.update_status(status)

        # Update Sidebar
        if self.sidebar:
            self.sidebar.update_data(
                status=status,
                branches=branches,
                stashes=stashes,
                tags=tags,
                commit_count=len(commits),
            )

        # Update Staging View
        if self.staging_view:
            self.staging_view.update_data(status)

        # Update History View
        if self.history_view:
            self.history_view.update_data(commits)

    # ---------------- Toolbar & Action Handlers ----------------

    def _action_open_repo_dialog(self) -> None:
        self.dialogs.show_open_repo_dialog(self.repo.root, self.open_repository)

    def _action_nav_commit(self) -> None:
        self.current_view = "status"
        if self.sidebar:
            self.sidebar.select_view_externally("status")
        self._switch_view("status")

    def _action_pull(self) -> None:
        if self.toolbar:
            self.toolbar.set_busy(True, "Pulling from remote...")

        def _cb(res: CommandResult):
            self._action_queue.put(("refresh_with_result", res))

        self.repo.pull(rebase=False, callback=_cb)

    def _action_push(self) -> None:
        status = self.repo.get_status()
        branch = status.current_branch or "HEAD"
        if self.toolbar:
            self.toolbar.set_busy(True, f"Pushing '{branch}'...")

        def _cb(res: CommandResult):
            self._action_queue.put(("refresh_with_result", res))

        self.repo.push(remote="origin", branch=status.current_branch, callback=_cb)

    def _action_fetch(self) -> None:
        if self.toolbar:
            self.toolbar.set_busy(True, "Fetching remotes...")

        def _cb(res: CommandResult):
            self._action_queue.put(("refresh_with_result", res))

        self.repo.fetch_all(callback=_cb)

    def _action_change_theme(self, theme_display_or_key: str) -> None:
        """Switch active theme dynamically and reload view styling."""
        self.theme_manager.apply_theme(theme_display_or_key, save_preference=True)
        if self.toolbar:
            self.toolbar.update_theme()
        self.refresh()

    def _action_branch_dialog(self) -> None:
        def _on_create(name: str, checkout: bool):
            res = self.repo.checkout_branch(name, create=True)
            if not res.success:
                self.dialogs.show_error("Branch Creation Failed", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_new_branch_dialog(_on_create)

    def _action_merge_dialog(self) -> None:
        branches = [b.name for b in self.repo.get_branches() if not b.is_current]
        if not branches:
            self.dialogs.show_info("Merge", "No other branches available to merge.")
            return

        def _on_merge(branch: str, no_ff: bool):
            res = self.repo.merge(branch, no_ff=no_ff)
            if not res.success:
                self.dialogs.show_error("Merge Conflict or Error", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_merge_dialog(branches, _on_merge)

    def _action_stash_dialog(self) -> None:
        def _on_stash(msg: str, keep_index: bool):
            res = self.repo.stash_save(message=msg, keep_index=keep_index)
            if not res.success:
                self.dialogs.show_error("Stash Failed", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_stash_dialog(_on_stash)

    def _action_discard_unstaged_dialog(self) -> None:
        def _on_confirm():
            # Discard all unstaged changes
            self.repo.runner.run(["restore", "."], cwd=self.repo.root)
            self.repo.runner.run(["clean", "-f", "-d"], cwd=self.repo.root)
            self.refresh()

        self.dialogs.show_confirm_discard_dialog("all unstaged files in the repository", _on_confirm)

    def _action_discard_single_file_dialog(self, delta: FileDelta) -> None:
        def _on_confirm():
            res = self.repo.discard_file(delta.path, is_untracked=delta.is_untracked)
            if not res.success:
                self.dialogs.show_error("Discard Failed", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_confirm_discard_dialog(delta.path, _on_confirm)

    def _action_checkout_branch(self, branch_name: str) -> None:
        res = self.repo.checkout_branch(branch_name)
        if not res.success:
            self.dialogs.show_error("Checkout Failed", res.stderr, res.stdout)
        self.refresh()

    def _action_delete_branch(self, branch_name: str) -> None:
        def _on_confirm():
            res = self.repo.delete_branch(branch_name)
            if not res.success:
                self.dialogs.show_error("Delete Branch Failed", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_confirm_discard_dialog(f"branch '{branch_name}'", _on_confirm)

    def _action_pop_stash(self, stash_id: str) -> None:
        res = self.repo.stash_pop(stash_id)
        if not res.success:
            self.dialogs.show_error("Stash Pop Conflict or Error", res.stderr, res.stdout)
        self.refresh()

    def _action_drop_stash(self, stash_id: str) -> None:
        def _on_confirm():
            res = self.repo.stash_drop(stash_id)
            if not res.success:
                self.dialogs.show_error("Drop Stash Failed", res.stderr, res.stdout)
            self.refresh()

        self.dialogs.show_confirm_discard_dialog(f"stash entry '{stash_id}'", _on_confirm)

    def _action_stage_file(self, path: str) -> None:
        res = self.repo.stage_file(path)
        if not res.success:
            self.dialogs.show_error("Stage Error", res.stderr)
        self.refresh()

    def _action_stage_all(self) -> None:
        res = self.repo.stage_all()
        if not res.success:
            self.dialogs.show_error("Stage All Error", res.stderr)
        self.refresh()

    def _action_unstage_file(self, path: str) -> None:
        res = self.repo.unstage_file(path)
        if not res.success:
            self.dialogs.show_error("Unstage Error", res.stderr)
        self.refresh()

    def _action_unstage_all(self) -> None:
        res = self.repo.unstage_all()
        if not res.success:
            self.dialogs.show_error("Unstage All Error", res.stderr)
        self.refresh()

    def _action_commit(self, subject: str, body: str, amend: bool, push: bool) -> None:
        res = self.repo.commit(subject=subject, body=body, amend=amend)
        if not res.success:
            self.dialogs.show_error("Commit Error", res.stderr, res.stdout)
            self.refresh()
            return

        if push:
            status = self.repo.get_status()
            self._action_push()
        else:
            self.refresh()

    def _handle_request_diff(self, file_path: str, is_staged: bool) -> str:
        return self.repo.get_diff(file_path=file_path, staged=is_staged)

    def _handle_request_commit_diff(self, commit_hash: str, file_path: Optional[str]) -> str:
        return self.repo.get_commit_diff(commit_hash=commit_hash, file_path=file_path)

    def _handle_request_commit_files(self, commit_hash: str) -> list[tuple[str, str]]:
        return self.repo.get_commit_files(commit_hash)

    def run(self) -> None:
        """Start the application main loop."""
        self.build_ui()
        dpg.show_viewport()

        # Initial data load if inside a git repo
        if self.repo.is_valid():
            self.refresh()

        while dpg.is_dearpygui_running():
            # Process thread queue messages (from background git workers)
            while not self._action_queue.empty():
                try:
                    action, payload = self._action_queue.get_nowait()
                    if action == "log_cmd" and self.console_view:
                        self.console_view.log_command(payload)
                    elif action == "refresh_with_result":
                        if self.toolbar:
                            self.toolbar.set_busy(False)
                        if not payload.success:
                            self.dialogs.show_error("Remote Git Error", payload.stderr, payload.stdout)
                        self.refresh()
                except queue.Empty:
                    break

            dpg.render_dearpygui_frame()

        dpg.destroy_context()

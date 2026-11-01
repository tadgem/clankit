"""File Status / Working Copy and Staging view matching SourceTree."""

from __future__ import annotations
from typing import Callable, List, Optional
import dearpygui.dearpygui as dpg
from clankit.git.models import FileDelta, RepoStatus
from clankit.ui.theme import SourceTreeColors, create_danger_button_theme, create_primary_button_theme
from clankit.ui.views.diff_viewer import DiffViewerComponent


class StagingViewComponent:
    """Manages staging area, unstaged files list, diff viewer, and commit composer."""

    def __init__(
        self,
        parent_tag: str,
        on_stage_file: Callable[[str], None],
        on_stage_all: Callable[[], None],
        on_unstage_file: Callable[[str], None],
        on_unstage_all: Callable[[], None],
        on_discard_file: Callable[[FileDelta], None],
        on_commit: Callable[[str, str, bool, bool], None],
        on_request_diff: Callable[[str, bool], str],
        tag: str = "staging_view_container",
    ):
        self.parent_tag = parent_tag
        self.on_stage_file = on_stage_file
        self.on_stage_all = on_stage_all
        self.on_unstage_file = on_unstage_file
        self.on_unstage_all = on_unstage_all
        self.on_discard_file = on_discard_file
        self.on_commit = on_commit
        self.on_request_diff = on_request_diff
        self.tag = tag

        self.unstaged_table_tag = "tbl_unstaged_files"
        self.staged_table_tag = "tbl_staged_files"
        self.commit_btn_tag = "btn_commit_action"
        self.subject_input_tag = "input_commit_subject"
        self.body_input_tag = "input_commit_body"
        self.amend_checkbox_tag = "chk_amend_commit"
        self.push_checkbox_tag = "chk_push_immediate"

        self.selected_file: Optional[str] = None
        self.selected_is_staged: bool = False
        self.diff_viewer: Optional[DiffViewerComponent] = None

        self._primary_theme = None
        self._danger_theme = None

    def build(self) -> None:
        """Construct the staging view layout."""
        self._primary_theme = create_primary_button_theme()
        self._danger_theme = create_danger_button_theme()

        with dpg.child_window(parent=self.parent_tag, tag=self.tag, border=False):
            # Split section for Staged / Unstaged tables
            with dpg.group(horizontal=True):
                # Unstaged Files Panel (Left)
                with dpg.child_window(width=480, height=220, border=True):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Unstaged Files", color=SourceTreeColors.TEXT_WHITE)
                        dpg.add_button(label="Stage All", callback=self.on_stage_all)
                    dpg.add_spacer(height=2)
                    with dpg.child_window(tag=self.unstaged_table_tag, border=False):
                        dpg.add_text("No unstaged changes", color=SourceTreeColors.TEXT_MUTED)

                # Staged Files Panel (Right)
                with dpg.child_window(width=-1, height=220, border=True):
                    with dpg.group(horizontal=True):
                        dpg.add_text("Staged Files (Index)", color=SourceTreeColors.TEXT_WHITE)
                        dpg.add_button(label="Unstage All", callback=self.on_unstage_all)
                    dpg.add_spacer(height=2)
                    with dpg.child_window(tag=self.staged_table_tag, border=False):
                        dpg.add_text("No staged changes", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_spacer(height=4)

            # Diff Viewer Section (Middle)
            diff_container_tag = f"{self.tag}_diff_section"
            with dpg.child_window(tag=diff_container_tag, height=230, border=True):
                self.diff_viewer = DiffViewerComponent(parent_tag=diff_container_tag, tag="staging_diff_viewer")
                self.diff_viewer.build()

            dpg.add_spacer(height=4)

            # Commit Composer Panel (Bottom)
            with dpg.child_window(height=-1, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text("Commit Changes", color=SourceTreeColors.TEXT_WHITE)
                    dpg.add_spacer(width=20)
                    dpg.add_checkbox(label="Amend last commit", tag=self.amend_checkbox_tag)
                    dpg.add_checkbox(label="Push changes immediately", tag=self.push_checkbox_tag)

                dpg.add_input_text(
                    tag=self.subject_input_tag,
                    hint="Commit summary / subject (required)",
                    width=-1,
                )
                dpg.add_input_text(
                    tag=self.body_input_tag,
                    hint="Extended description (optional)...",
                    multiline=True,
                    height=55,
                    width=-1,
                )

                dpg.add_spacer(height=4)
                with dpg.group(horizontal=True):
                    btn_commit = dpg.add_button(
                        label="Commit",
                        tag=self.commit_btn_tag,
                        width=120,
                        callback=self._handle_commit_click,
                    )
                    dpg.bind_item_theme(btn_commit, self._primary_theme)

    def reset(self) -> None:
        """Reset state when switching repositories."""
        self.selected_file = None
        self.selected_is_staged = False
        if dpg.does_item_exist(self.subject_input_tag):
            dpg.set_value(self.subject_input_tag, "")
        if dpg.does_item_exist(self.body_input_tag):
            dpg.set_value(self.body_input_tag, "")
        if dpg.does_item_exist(self.amend_checkbox_tag):
            dpg.set_value(self.amend_checkbox_tag, False)
        if self.diff_viewer:
            self.diff_viewer.set_diff("", file_name="")

    def update_data(self, status: RepoStatus) -> None:
        """Update file lists and refresh the diff view."""
        # 1. Update Unstaged
        dpg.delete_item(self.unstaged_table_tag, children_only=True)
        unstaged = status.unstaged_files
        if not unstaged:
            dpg.add_text("No unstaged changes", parent=self.unstaged_table_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for delta in unstaged:
                self._build_unstaged_row(delta)

        # 2. Update Staged
        dpg.delete_item(self.staged_table_tag, children_only=True)
        staged = status.staged_files
        if not staged:
            dpg.add_text("No staged changes", parent=self.staged_table_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for delta in staged:
                self._build_staged_row(delta)

        # 3. Update Commit Button label
        staged_count = len(staged)
        btn_label = f"Commit ({staged_count})" if staged_count > 0 else "Commit"
        dpg.configure_item(self.commit_btn_tag, label=btn_label)

        # 4. Refresh selected file diff if still relevant in this repo
        matching_file = next((f for f in status.files if f.path == self.selected_file), None) if self.selected_file else None
        if matching_file:
            self._display_file_diff(self.selected_file, self.selected_is_staged)
        else:
            self.selected_file = None
            if self.diff_viewer:
                self.diff_viewer.set_diff("", file_name="")

    def _build_unstaged_row(self, delta: FileDelta) -> None:
        status_letter = delta.worktree_status if delta.worktree_status != " " else delta.index_status
        status_color = self._get_status_color(status_letter)

        row_group = dpg.add_group(parent=self.unstaged_table_tag, horizontal=True)
        dpg.add_text(f"[{status_letter}]", parent=row_group, color=status_color)
        dpg.add_selectable(
            parent=row_group,
            label=delta.path,
            user_data=(delta.path, False),
            callback=self._on_select_file,
            span_columns=True,
        )
        dpg.add_button(
            parent=row_group,
            label="Stage",
            user_data=delta.path,
            callback=lambda s, a, u: self.on_stage_file(u),
        )
        discard_btn = dpg.add_button(
            parent=row_group,
            label="Discard",
            user_data=delta,
            callback=lambda s, a, u: self.on_discard_file(u),
        )
        dpg.bind_item_theme(discard_btn, self._danger_theme)

    def _build_staged_row(self, delta: FileDelta) -> None:
        status_letter = delta.index_status
        status_color = self._get_status_color(status_letter)

        row_group = dpg.add_group(parent=self.staged_table_tag, horizontal=True)
        dpg.add_text(f"[{status_letter}]", parent=row_group, color=status_color)
        dpg.add_selectable(
            parent=row_group,
            label=delta.path,
            user_data=(delta.path, True),
            callback=self._on_select_file,
            span_columns=True,
        )
        dpg.add_button(
            parent=row_group,
            label="Unstage",
            user_data=delta.path,
            callback=lambda s, a, u: self.on_unstage_file(u),
        )

    def _get_status_color(self, letter: str) -> tuple:
        if letter == "M":
            return SourceTreeColors.STATUS_MODIFIED
        if letter == "A":
            return SourceTreeColors.STATUS_ADDED
        if letter == "D":
            return SourceTreeColors.STATUS_DELETED
        if letter == "?":
            return SourceTreeColors.STATUS_UNTRACKED
        if letter == "U":
            return SourceTreeColors.STATUS_CONFLICT
        return SourceTreeColors.TEXT_NORMAL

    def _on_select_file(self, sender, app_data, user_data: tuple[str, bool]) -> None:
        file_path, is_staged = user_data
        self.selected_file = file_path
        self.selected_is_staged = is_staged
        self._display_file_diff(file_path, is_staged)

    def _display_file_diff(self, file_path: str, is_staged: bool) -> None:
        if not self.diff_viewer:
            return
        diff_text = self.on_request_diff(file_path, is_staged)
        staged_tag = "(Staged Index)" if is_staged else "(Working Tree)"
        self.diff_viewer.set_diff(diff_text, file_name=f"{file_path} {staged_tag}")

    def _handle_commit_click(self) -> None:
        subject = dpg.get_value(self.subject_input_tag).strip()
        body = dpg.get_value(self.body_input_tag).strip()
        amend = dpg.get_value(self.amend_checkbox_tag)
        push = dpg.get_value(self.push_checkbox_tag)

        if not subject and not amend:
            return

        self.on_commit(subject, body, amend, push)
        # Clear fields on successful submit
        dpg.set_value(self.subject_input_tag, "")
        dpg.set_value(self.body_input_tag, "")
        dpg.set_value(self.amend_checkbox_tag, False)

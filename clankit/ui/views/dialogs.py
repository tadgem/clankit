"""Modal dialogs for user interactions (Branching, Merging, Stashing, Errors)."""

from __future__ import annotations
from typing import Callable, List, Optional
import dearpygui.dearpygui as dpg
from clankit.ui.theme import SourceTreeColors, create_danger_button_theme, create_primary_button_theme


class DialogManager:
    """Creates and manages modal popups in Dear PyGui."""

    def __init__(self):
        self._primary_theme = None
        self._danger_theme = None

    def _ensure_themes(self):
        if self._primary_theme is None:
            self._primary_theme = create_primary_button_theme()
        if self._danger_theme is None:
            self._danger_theme = create_danger_button_theme()

    def show_error(self, title: str, message: str, details: str = "") -> None:
        """Display an error modal."""
        modal_tag = "modal_error"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label=f"Git Error - {title}",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=520,
            height=320,
            pos=[250, 150],
        ):
            dpg.add_text(message, color=SourceTreeColors.STATUS_DELETED)
            dpg.add_spacer(height=6)
            if details:
                dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    default_value=details,
                    width=-1,
                    height=200,
                )
            dpg.add_spacer(height=8)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Dismiss", width=100, callback=lambda: dpg.delete_item(modal_tag))

    def show_info(self, title: str, message: str) -> None:
        """Display an information modal."""
        modal_tag = "modal_info"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label=title,
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=400,
            height=150,
            pos=[300, 200],
        ):
            dpg.add_text(message)
            dpg.add_spacer(height=16)
            dpg.add_button(label="OK", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def show_new_branch_dialog(self, on_create: Callable[[str, bool], None]) -> None:
        """Prompt to create a new branch."""
        self._ensure_themes()
        modal_tag = "modal_new_branch"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label="Create New Branch",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=420,
            height=180,
            pos=[300, 200],
        ):
            dpg.add_text("Branch Name:")
            input_tag = dpg.add_input_text(hint="feature/new-feature", width=-1)
            checkout_tag = dpg.add_checkbox(label="Checkout branch immediately", default_value=True)

            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                btn_create = dpg.add_button(
                    label="Create Branch",
                    width=120,
                    callback=lambda: self._submit_branch(modal_tag, input_tag, checkout_tag, on_create),
                )
                dpg.bind_item_theme(btn_create, self._primary_theme)
                dpg.add_button(label="Cancel", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def _submit_branch(self, modal_tag: str, input_tag: int, checkout_tag: int, callback: Callable) -> None:
        name = dpg.get_value(input_tag).strip()
        do_checkout = dpg.get_value(checkout_tag)
        if not name:
            return
        dpg.delete_item(modal_tag)
        callback(name, do_checkout)

    def show_merge_dialog(self, branches: List[str], on_merge: Callable[[str, bool], None]) -> None:
        """Prompt to merge another branch into current branch."""
        self._ensure_themes()
        modal_tag = "modal_merge"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label="Merge Branch",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=420,
            height=200,
            pos=[300, 200],
        ):
            dpg.add_text("Select branch to merge into current:")
            combo_tag = dpg.add_combo(items=branches, default_value=branches[0] if branches else "", width=-1)
            noff_tag = dpg.add_checkbox(label="Create a commit even if fast-forward (--no-ff)", default_value=True)

            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                btn_merge = dpg.add_button(
                    label="Merge",
                    width=100,
                    callback=lambda: self._submit_merge(modal_tag, combo_tag, noff_tag, on_merge),
                )
                dpg.bind_item_theme(btn_merge, self._primary_theme)
                dpg.add_button(label="Cancel", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def _submit_merge(self, modal_tag: str, combo_tag: int, noff_tag: int, callback: Callable) -> None:
        branch = dpg.get_value(combo_tag)
        no_ff = dpg.get_value(noff_tag)
        if not branch:
            return
        dpg.delete_item(modal_tag)
        callback(branch, no_ff)

    def show_stash_dialog(self, on_stash: Callable[[str, bool], None]) -> None:
        """Prompt to stash changes."""
        self._ensure_themes()
        modal_tag = "modal_stash"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label="Stash Working Copy Changes",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=420,
            height=180,
            pos=[300, 200],
        ):
            dpg.add_text("Stash Message (optional):")
            input_tag = dpg.add_input_text(hint="WIP changes...", width=-1)
            keep_index_tag = dpg.add_checkbox(label="Keep staged changes in index", default_value=False)

            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                btn_stash = dpg.add_button(
                    label="Stash",
                    width=100,
                    callback=lambda: self._submit_stash(modal_tag, input_tag, keep_index_tag, on_stash),
                )
                dpg.bind_item_theme(btn_stash, self._primary_theme)
                dpg.add_button(label="Cancel", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def _submit_stash(self, modal_tag: str, input_tag: int, keep_tag: int, callback: Callable) -> None:
        msg = dpg.get_value(input_tag).strip()
        keep = dpg.get_value(keep_tag)
        dpg.delete_item(modal_tag)
        callback(msg, keep)

    def show_confirm_discard_dialog(self, target: str, on_confirm: Callable[[], None]) -> None:
        """Prompt for confirmation before discarding changes."""
        self._ensure_themes()
        modal_tag = "modal_discard_confirm"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label="Discard Changes Confirmation",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=420,
            height=160,
            pos=[300, 200],
        ):
            dpg.add_text(f"Are you sure you want to discard changes in:\n{target}?", color=SourceTreeColors.STATUS_DELETED)
            dpg.add_text("This action cannot be undone!", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                btn_discard = dpg.add_button(
                    label="Discard Changes",
                    width=140,
                    callback=lambda: (dpg.delete_item(modal_tag), on_confirm()),
                )
                dpg.bind_item_theme(btn_discard, self._danger_theme)
                dpg.add_button(label="Cancel", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def show_open_repo_dialog(self, current_path: str, on_open: Callable[[str], None]) -> None:
        """Prompt to open another local Git repository directory."""
        self._ensure_themes()
        modal_tag = "modal_open_repo"
        if dpg.does_item_exist(modal_tag):
            dpg.delete_item(modal_tag)

        with dpg.window(
            label="Open Local Git Repository",
            tag=modal_tag,
            modal=True,
            show=True,
            no_resize=True,
            width=500,
            height=160,
            pos=[280, 200],
        ):
            dpg.add_text("Repository Directory Path:")
            input_tag = dpg.add_input_text(default_value=current_path, width=-1)

            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                btn_open = dpg.add_button(
                    label="Open Repository",
                    width=140,
                    callback=lambda: self._submit_open_repo(modal_tag, input_tag, on_open),
                )
                dpg.bind_item_theme(btn_open, self._primary_theme)
                dpg.add_button(label="Cancel", width=80, callback=lambda: dpg.delete_item(modal_tag))

    def _submit_open_repo(self, modal_tag: str, input_tag: int, callback: Callable) -> None:
        path = dpg.get_value(input_tag).strip()
        if not path:
            return
        dpg.delete_item(modal_tag)
        callback(path)

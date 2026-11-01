"""Syntax-highlighted unified diff viewer for Dear PyGui."""

from __future__ import annotations
import dearpygui.dearpygui as dpg
from clankit.ui.theme import SourceTreeColors


class DiffViewerComponent:
    """Renders unified diffs with line-by-line syntax coloration."""

    def __init__(self, parent_tag: str, tag: Optional[str] = None):
        self.parent_tag = parent_tag
        self.tag = tag or f"{parent_tag}_diff_viewer"
        self.scroll_tag = f"{self.tag}_scroll"

    def build(self) -> None:
        """Construct the container widgets."""
        with dpg.child_window(
            parent=self.parent_tag,
            tag=self.tag,
            border=True,
            horizontal_scrollbar=True,
        ):
            dpg.add_text("Select a file to inspect diff", tag=f"{self.tag}_placeholder", color=SourceTreeColors.TEXT_MUTED)

    def set_diff(self, raw_diff: str, file_name: str = "") -> None:
        """Update diff content with syntax-highlighted lines."""
        # Clear previous contents of the diff viewer
        dpg.delete_item(self.tag, children_only=True)

        if not raw_diff or not raw_diff.strip():
            dpg.add_text(
                f"No changes detected in '{file_name}'" if file_name else "No changes to display.",
                parent=self.tag,
                color=SourceTreeColors.TEXT_MUTED,
            )
            return

        lines = raw_diff.splitlines()
        # Cap display at 3000 lines to preserve instant 60 FPS rendering on huge diffs
        display_lines = lines[:3000]
        truncated = len(lines) > 3000

        for line in display_lines:
            if line.startswith("+++") or line.startswith("---") or line.startswith("diff --git"):
                dpg.add_text(line, parent=self.tag, color=SourceTreeColors.DIFF_META_TEXT)
            elif line.startswith("@@"):
                dpg.add_text(line, parent=self.tag, color=SourceTreeColors.DIFF_HEADER_TEXT)
            elif line.startswith("+"):
                dpg.add_text(line, parent=self.tag, color=SourceTreeColors.DIFF_ADD_TEXT)
            elif line.startswith("-"):
                dpg.add_text(line, parent=self.tag, color=SourceTreeColors.DIFF_DEL_TEXT)
            else:
                dpg.add_text(line, parent=self.tag, color=SourceTreeColors.TEXT_NORMAL)

        if truncated:
            dpg.add_text(
                f"\n... Diff truncated ({len(lines) - 3000} more lines). Showing first 3000 lines.",
                parent=self.tag,
                color=SourceTreeColors.TEXT_MUTED,
            )

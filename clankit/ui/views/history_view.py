"""History / Visual Commit Graph view matching SourceTree."""

from __future__ import annotations
from typing import Callable, List, Optional, Tuple
import dearpygui.dearpygui as dpg
from clankit.git.models import CommitNode
from clankit.ui.graph_renderer import CommitGraphLayout
from clankit.ui.theme import SourceTreeColors
from clankit.ui.views.diff_viewer import DiffViewerComponent


class HistoryViewComponent:
    """Renders the topological visual commit DAG table and commit inspector."""

    def __init__(
        self,
        parent_tag: str,
        on_request_commit_diff: Callable[[str, Optional[str]], str],
        on_request_commit_files: Callable[[str], List[Tuple[str, str]]],
        tag: str = "history_view_container",
    ):
        self.parent_tag = parent_tag
        self.on_request_commit_diff = on_request_commit_diff
        self.on_request_commit_files = on_request_commit_files
        self.tag = tag

        self.commits_table_tag = "tbl_commit_history"
        self.filter_input_tag = "input_commit_filter"
        self.commit_meta_tag = "txt_commit_metadata"
        self.commit_body_tag = "txt_commit_body"
        self.commit_files_list_tag = "list_commit_files"

        self.commits: List[CommitNode] = []
        self.selected_commit: Optional[CommitNode] = None
        self.diff_viewer: Optional[DiffViewerComponent] = None

    def build(self) -> None:
        """Construct the history view layout."""
        with dpg.child_window(parent=self.parent_tag, tag=self.tag, border=False, show=False):
            # Search & Filter bar
            with dpg.group(horizontal=True):
                dpg.add_text("Filter Commits:", color=SourceTreeColors.TEXT_MUTED)
                dpg.add_input_text(
                    tag=self.filter_input_tag,
                    hint="Search message, author, or SHA...",
                    width=350,
                    callback=self._on_filter_changed,
                )

            dpg.add_spacer(height=3)

            # Top Table: Commit History Log with Graph
            table_container_tag = f"{self.tag}_table_container"
            with dpg.child_window(tag=table_container_tag, height=270, border=True):
                with dpg.table(
                    tag=self.commits_table_tag,
                    header_row=True,
                    resizable=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    row_background=True,
                    scrollY=True,
                ):
                    dpg.add_table_column(label="Graph", width_fixed=True, init_width_or_weight=65)
                    dpg.add_table_column(label="Description", init_width_or_weight=380)
                    dpg.add_table_column(label="Author", width_fixed=True, init_width_or_weight=130)
                    dpg.add_table_column(label="Date", width_fixed=True, init_width_or_weight=140)
                    dpg.add_table_column(label="SHA", width_fixed=True, init_width_or_weight=75)

            dpg.add_spacer(height=4)

            # Bottom Section: Selected Commit Details & Diff Viewer Split
            with dpg.group(horizontal=True):
                # Left details pane
                with dpg.child_window(width=420, height=-1, border=True):
                    dpg.add_text("Commit Details", color=SourceTreeColors.TEXT_WHITE)
                    dpg.add_text("", tag=self.commit_meta_tag, color=SourceTreeColors.TEXT_MUTED)
                    dpg.add_input_text(
                        tag=self.commit_body_tag,
                        multiline=True,
                        readonly=True,
                        height=90,
                        width=-1,
                        default_value="Select a commit above to inspect details.",
                    )
                    dpg.add_spacer(height=4)
                    dpg.add_text("Modified Files in Commit:", color=SourceTreeColors.TEXT_WHITE)
                    with dpg.child_window(tag=self.commit_files_list_tag, height=-1, border=False):
                        dpg.add_text("No commit selected", color=SourceTreeColors.TEXT_MUTED)

                # Right diff pane
                diff_container_tag = f"{self.tag}_commit_diff_container"
                with dpg.child_window(tag=diff_container_tag, width=-1, height=-1, border=True):
                    self.diff_viewer = DiffViewerComponent(parent_tag=diff_container_tag, tag="history_diff_viewer")
                    self.diff_viewer.build()

    def update_data(self, commits: List[CommitNode]) -> None:
        """Update commit history and compute graph layout."""
        self.commits = commits
        CommitGraphLayout.layout(self.commits)
        self._populate_table(self.commits)

    def _on_filter_changed(self, sender, filter_text: str) -> None:
        filter_text = filter_text.strip().lower()
        if not filter_text:
            self._populate_table(self.commits)
            return

        filtered = [
            c
            for c in self.commits
            if filter_text in c.subject.lower()
            or filter_text in c.author_name.lower()
            or filter_text in c.short_hash.lower()
            or any(filter_text in r.lower() for r in c.refs)
        ]
        self._populate_table(filtered)

    def _populate_table(self, commit_list: List[CommitNode]) -> None:
        dpg.delete_item(self.commits_table_tag, children_only=True)

        for commit in commit_list:
            row_tag = f"commit_row_{commit.hash}"
            with dpg.table_row(parent=self.commits_table_tag, tag=row_tag):
                # 1. Graph representation
                graph_glyph = CommitGraphLayout.format_ascii_graph(commit)
                lane_color = CommitGraphLayout.get_lane_color(commit.lane)
                dpg.add_text(graph_glyph, color=lane_color)

                # 2. Description with ref badges
                with dpg.group(horizontal=True):
                    if commit.refs:
                        for ref in commit.refs:
                            ref_color = SourceTreeColors.PRIMARY_BLUE if "HEAD" in ref else SourceTreeColors.STATUS_MODIFIED
                            dpg.add_text(f"[{ref}]", color=ref_color)
                    dpg.add_selectable(
                        label=commit.subject,
                        user_data=commit,
                        callback=self._on_select_commit,
                        span_columns=True,
                    )

                # 3. Author
                dpg.add_text(commit.author_name)

                # 4. Date
                # Format ISO date nicely
                clean_date = commit.date.split("T")[0] if "T" in commit.date else commit.date[:16]
                dpg.add_text(clean_date, color=SourceTreeColors.TEXT_MUTED)

                # 5. SHA
                dpg.add_text(commit.short_hash, color=SourceTreeColors.DIFF_HEADER_TEXT)

        # Select first commit by default if none selected
        if commit_list and self.selected_commit is None:
            self._display_commit_details(commit_list[0])

    def _on_select_commit(self, sender, app_data, user_data: CommitNode) -> None:
        self._display_commit_details(user_data)

    def _display_commit_details(self, commit: CommitNode) -> None:
        self.selected_commit = commit

        meta_lines = [
            f"Commit: {commit.hash}",
            f"Author: {commit.author_name} <{commit.author_email}>",
            f"Date:   {commit.date}",
        ]
        if commit.parents:
            meta_lines.append(f"Parents: {' '.join(p[:7] for p in commit.parents)}")
        dpg.set_value(self.commit_meta_tag, "\n".join(meta_lines))

        full_message = f"{commit.subject}\n\n{commit.body}".strip()
        dpg.set_value(self.commit_body_tag, full_message)

        # Populate files changed in commit
        dpg.delete_item(self.commit_files_list_tag, children_only=True)
        files = self.on_request_commit_files(commit.hash)
        if not files:
            dpg.add_text("No changed files", parent=self.commit_files_list_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for status, path in files:
                color = SourceTreeColors.STATUS_MODIFIED if status == "M" else (
                    SourceTreeColors.STATUS_ADDED if status == "A" else SourceTreeColors.STATUS_DELETED
                )
                with dpg.group(parent=self.commit_files_list_tag, horizontal=True):
                    dpg.add_text(f"[{status}]", color=color)
                    dpg.add_selectable(
                        label=path,
                        user_data=(commit.hash, path),
                        callback=lambda s, a, u: self._on_select_commit_file(u[0], u[1]),
                    )

        # Show whole commit diff by default
        diff_text = self.on_request_commit_diff(commit.hash, None)
        if self.diff_viewer:
            self.diff_viewer.set_diff(diff_text, file_name=f"Commit {commit.short_hash}")

    def _on_select_commit_file(self, commit_hash: str, file_path: str) -> None:
        diff_text = self.on_request_commit_diff(commit_hash, file_path)
        if self.diff_viewer:
            self.diff_viewer.set_diff(diff_text, file_name=f"{file_path} ({commit_hash[:7]})")

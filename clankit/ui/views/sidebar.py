"""Left navigation sidebar matching SourceTree workspace hierarchy."""

from __future__ import annotations
from typing import Callable, List, Optional
import dearpygui.dearpygui as dpg
from clankit.git.models import BranchInfo, RepoStatus, StashInfo, TagInfo
from clankit.ui.theme import SourceTreeColors


class SidebarComponent:
    """Renders the left navigation sidebar (Workspace, Branches, Remotes, Stashes, Tags)."""

    def __init__(
        self,
        parent_tag: str,
        on_select_view: Callable[[str], None],  # 'status' or 'history'
        on_checkout_branch: Callable[[str], None],
        on_delete_branch: Callable[[str], None],
        on_pop_stash: Callable[[str], None],
        on_drop_stash: Callable[[str], None],
        tag: str = "sidebar_container",
    ):
        self.parent_tag = parent_tag
        self.on_select_view = on_select_view
        self.on_checkout_branch = on_checkout_branch
        self.on_delete_branch = on_delete_branch
        self.on_pop_stash = on_pop_stash
        self.on_drop_stash = on_drop_stash
        self.tag = tag

        self.file_status_label_tag = "sb_status_label"
        self.history_label_tag = "sb_history_label"
        self.branches_tree_tag = "sb_branches_tree"
        self.remotes_tree_tag = "sb_remotes_tree"
        self.stashes_tree_tag = "sb_stashes_tree"
        self.tags_tree_tag = "sb_tags_tree"

    def build(self) -> None:
        """Construct the sidebar tree views."""
        with dpg.child_window(
            parent=self.parent_tag,
            tag=self.tag,
            width=240,
            border=True,
        ):
            # 1. WORKSPACE
            with dpg.tree_node(label="WORKSPACE", default_open=True):
                dpg.add_selectable(
                    label="File Status",
                    tag=self.file_status_label_tag,
                    default_value=True,
                    callback=lambda: self._select_view("status"),
                )
                dpg.add_selectable(
                    label="History",
                    tag=self.history_label_tag,
                    callback=lambda: self._select_view("history"),
                )

            dpg.add_spacer(height=4)

            # 2. BRANCHES
            with dpg.tree_node(label="BRANCHES", tag=self.branches_tree_tag, default_open=True):
                dpg.add_text("No branches", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_spacer(height=4)

            # 3. REMOTES
            with dpg.tree_node(label="REMOTES", tag=self.remotes_tree_tag, default_open=True):
                dpg.add_text("No remotes", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_spacer(height=4)

            # 4. STASHES
            with dpg.tree_node(label="STASHES", tag=self.stashes_tree_tag, default_open=False):
                dpg.add_text("No stashes", color=SourceTreeColors.TEXT_MUTED)

            dpg.add_spacer(height=4)

            # 5. TAGS
            with dpg.tree_node(label="TAGS", tag=self.tags_tree_tag, default_open=False):
                dpg.add_text("No tags", color=SourceTreeColors.TEXT_MUTED)

    def _select_view(self, view_name: str) -> None:
        if view_name == "status":
            dpg.set_value(self.file_status_label_tag, True)
            dpg.set_value(self.history_label_tag, False)
        else:
            dpg.set_value(self.file_status_label_tag, False)
            dpg.set_value(self.history_label_tag, True)
        self.on_select_view(view_name)

    def select_view_externally(self, view_name: str) -> None:
        self._select_view(view_name)

    def update_data(
        self,
        status: RepoStatus,
        branches: List[BranchInfo],
        stashes: List[StashInfo],
        tags: List[TagInfo],
        commit_count: int = 0,
    ) -> None:
        """Refresh sidebar tree contents."""
        # 1. Update Workspace counts
        uncommitted_count = len(status.files)
        status_label = f"File Status ({uncommitted_count})" if uncommitted_count > 0 else "File Status"
        dpg.configure_item(self.file_status_label_tag, label=status_label)

        history_label = f"History ({commit_count})" if commit_count > 0 else "History"
        dpg.configure_item(self.history_label_tag, label=history_label)

        # 2. Update Local Branches
        dpg.delete_item(self.branches_tree_tag, children_only=True)
        local_branches = [b for b in branches if not b.is_remote]
        if not local_branches:
            dpg.add_text("No local branches", parent=self.branches_tree_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for b in local_branches:
                prefix = "* " if b.is_current else "  "
                label = f"{prefix}{b.name}"
                color = SourceTreeColors.PRIMARY_BLUE if b.is_current else SourceTreeColors.TEXT_NORMAL
                item_group = dpg.add_group(parent=self.branches_tree_tag, horizontal=True)
                dpg.add_selectable(
                    parent=item_group,
                    label=label,
                    default_value=b.is_current,
                    user_data=b.name,
                    callback=lambda s, a, u: self.on_checkout_branch(u),
                )
                if not b.is_current:
                    dpg.add_button(
                        parent=item_group,
                        label="x",
                        user_data=b.name,
                        callback=lambda s, a, u: self.on_delete_branch(u),
                    )

        # 3. Update Remotes
        dpg.delete_item(self.remotes_tree_tag, children_only=True)
        remote_branches = [b for b in branches if b.is_remote]
        if not remote_branches:
            dpg.add_text("No remotes configured", parent=self.remotes_tree_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            # Group by remote name
            remotes_map: dict[str, list[BranchInfo]] = {}
            for b in remote_branches:
                r_name = b.remote_name or "remotes"
                remotes_map.setdefault(r_name, []).append(b)

            for r_name, r_branches in remotes_map.items():
                with dpg.tree_node(parent=self.remotes_tree_tag, label=r_name, default_open=True):
                    for b in r_branches:
                        dpg.add_selectable(
                            label=f"  {b.short_name}",
                            user_data=b.name,
                            callback=lambda s, a, u: self.on_checkout_branch(u),
                        )

        # 4. Update Stashes
        dpg.delete_item(self.stashes_tree_tag, children_only=True)
        if not stashes:
            dpg.add_text("No stashes", parent=self.stashes_tree_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for s in stashes:
                stash_group = dpg.add_group(parent=self.stashes_tree_tag, horizontal=True)
                dpg.add_text(parent=stash_group, label=f"{s.id}: {s.message[:25]}")
                dpg.add_button(
                    parent=stash_group,
                    label="Pop",
                    user_data=s.id,
                    callback=lambda s_btn, a, u: self.on_pop_stash(u),
                )
                dpg.add_button(
                    parent=stash_group,
                    label="x",
                    user_data=s.id,
                    callback=lambda s_btn, a, u: self.on_drop_stash(u),
                )

        # 5. Update Tags
        dpg.delete_item(self.tags_tree_tag, children_only=True)
        if not tags:
            dpg.add_text("No tags", parent=self.tags_tree_tag, color=SourceTreeColors.TEXT_MUTED)
        else:
            for t in tags:
                dpg.add_text(f"● {t.name}", parent=self.tags_tree_tag, color=SourceTreeColors.PRIMARY_HOVER)

"""Tests for progress spinner, loading indicator, and toolbar busy state."""

import dearpygui.dearpygui as dpg
from clankit.git.models import RepoStatus
from clankit.ui.views.toolbar import ToolbarComponent


def test_toolbar_progress_and_busy_state():
    dpg.create_context()
    try:
        with dpg.window(label="TestWindow", tag="test_window"):
            container = dpg.add_group(tag="tb_container")

        tb = ToolbarComponent(
            parent_tag=container,
            on_open_repo=lambda: None,
            on_refresh=lambda: None,
            on_commit_click=lambda: None,
            on_pull_click=lambda: None,
            on_push_click=lambda: None,
            on_fetch_click=lambda: None,
            on_branch_click=lambda: None,
            on_merge_click=lambda: None,
            on_stash_click=lambda: None,
            on_discard_click=lambda: None,
            get_repo_path=lambda: "/test/repo",
            on_theme_change=lambda t: None,
        )
        tb.build()

        # Check initial state: progress group is hidden
        assert dpg.does_item_exist(tb.progress_group_tag)
        assert dpg.does_item_exist(tb.progress_spinner_tag)
        assert dpg.does_item_exist(tb.progress_text_tag)
        assert not dpg.is_item_visible(tb.progress_group_tag)

        # Trigger busy state for pushing
        tb.set_busy(True, "Pushing to origin...")
        assert dpg.get_value(tb.progress_text_tag) == "Pushing to origin..."
        assert dpg.get_item_configuration(tb.pull_btn_tag)["enabled"] is False
        assert dpg.get_item_configuration(tb.push_btn_tag)["enabled"] is False
        assert dpg.get_item_configuration(tb.fetch_btn_tag)["enabled"] is False

        # Trigger idle state
        tb.set_busy(False)
        assert dpg.get_item_configuration(tb.pull_btn_tag)["enabled"] is True
        assert dpg.get_item_configuration(tb.push_btn_tag)["enabled"] is True
        assert dpg.get_item_configuration(tb.fetch_btn_tag)["enabled"] is True

        # Test updating status with ahead/behind badges
        st = RepoStatus(
            root_dir="/test/repo",
            current_branch="main",
            ahead=2,
            behind=1,
            files=[],
        )
        tb.update_status(st)
        assert "Push (2)" in dpg.get_item_configuration(tb.push_btn_tag)["label"]
        assert "Pull (1)" in dpg.get_item_configuration(tb.pull_btn_tag)["label"]
        assert "main (⇡2 ⇣1)" in dpg.get_value(tb.status_text_tag)

        # Test updating theme
        tb.update_theme()
    finally:
        dpg.destroy_context()

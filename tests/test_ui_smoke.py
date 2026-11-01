"""Smoke test verifying Dear PyGui UI lifecycle, frame rendering, staging actions, and repository switching."""

import os
import shutil
import subprocess
import tempfile
import dearpygui.dearpygui as dpg
from clankit.ui.app import ClankitApp


def test_ui_build_render_and_repo_switch():
    tmp_dir1 = tempfile.mkdtemp(prefix="clankit_ui_smoke1_")
    tmp_dir2 = tempfile.mkdtemp(prefix="clankit_ui_smoke2_")
    try:
        # Setup Repo 1
        subprocess.run(["git", "init", "-b", "main"], cwd=tmp_dir1, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Smoke User 1"], cwd=tmp_dir1, check=True)
        subprocess.run(["git", "config", "user.email", "smoke1@example.com"], cwd=tmp_dir1, check=True)

        with open(os.path.join(tmp_dir1, "file1.txt"), "w") as f:
            f.write("Line 1 from Repo 1\n")
        subprocess.run(["git", "add", "."], cwd=tmp_dir1, check=True)
        subprocess.run(["git", "commit", "-m", "Commit from Repo One"], cwd=tmp_dir1, check=True)

        # Create an unstaged change in Repo 1
        with open(os.path.join(tmp_dir1, "file1.txt"), "a") as f:
            f.write("Uncommitted line in Repo 1\n")

        # Setup Repo 2
        subprocess.run(["git", "init", "-b", "main"], cwd=tmp_dir2, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Smoke User 2"], cwd=tmp_dir2, check=True)
        subprocess.run(["git", "config", "user.email", "smoke2@example.com"], cwd=tmp_dir2, check=True)

        with open(os.path.join(tmp_dir2, "file2.txt"), "w") as f:
            f.write("Line 1 from Repo 2\n")
        subprocess.run(["git", "add", "."], cwd=tmp_dir2, check=True)
        subprocess.run(["git", "commit", "-m", "Commit from Repo Two"], cwd=tmp_dir2, check=True)

        # 1. Initialize ClankitApp with Repo 1
        app = ClankitApp(initial_path=tmp_dir1)
        app.build_ui()
        dpg.show_viewport()

        # Load initial repository state
        app.refresh()

        # Check Repo 1 state
        assert len(app.history_view.commits) == 1
        assert app.history_view.commits[0].subject == "Commit from Repo One"
        assert app.history_view.selected_commit.subject == "Commit from Repo One"
        cols_r1 = dpg.get_item_children(app.history_view.commits_table_tag, 0)
        assert len(cols_r1) == 5

        # Verify unstaged files in staging view
        st1 = app.repo.get_status()
        assert len(st1.unstaged_files) == 1
        assert st1.unstaged_files[0].path == "file1.txt"
        assert len(st1.staged_files) == 0

        # Test staging via the staging view action callback
        app.staging_view.on_stage_file("file1.txt")
        dpg.render_dearpygui_frame()

        st1_after_stage = app.repo.get_status()
        assert len(st1_after_stage.unstaged_files) == 0
        assert len(st1_after_stage.staged_files) == 1
        assert st1_after_stage.staged_files[0].path == "file1.txt"

        # Test unstaging via the staging view action callback
        app.staging_view.on_unstage_file("file1.txt")
        dpg.render_dearpygui_frame()

        st1_after_unstage = app.repo.get_status()
        assert len(st1_after_unstage.unstaged_files) == 1
        assert len(st1_after_unstage.staged_files) == 0

        # Render 3 frames
        for _ in range(3):
            dpg.render_dearpygui_frame()

        # 2. Switch repository to Repo 2 dynamically while app is running
        app.open_repository(tmp_dir2)

        # Check Repo 2 state
        assert len(app.history_view.commits) == 1
        assert app.history_view.commits[0].subject == "Commit from Repo Two"
        assert app.history_view.selected_commit.subject == "Commit from Repo Two"
        assert "Commit from Repo Two" in dpg.get_value(app.history_view.commit_body_tag)

        # Ensure table columns are STILL preserved in slot 0
        cols_r2 = dpg.get_item_children(app.history_view.commits_table_tag, 0)
        assert len(cols_r2) == 5

        # Ensure table rows in slot 1 are updated
        rows_r2 = dpg.get_item_children(app.history_view.commits_table_tag, 1)
        assert len(rows_r2) == 1

        # Switch to history view and back
        app._switch_view("history")
        app._switch_view("status")

        # Render 3 frames with new repository active
        for _ in range(3):
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
    finally:
        shutil.rmtree(tmp_dir1, ignore_errors=True)
        shutil.rmtree(tmp_dir2, ignore_errors=True)

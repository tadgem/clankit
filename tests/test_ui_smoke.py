"""Smoke test verifying Dear PyGui UI lifecycle and frame rendering."""

import os
import subprocess
import tempfile
import dearpygui.dearpygui as dpg
from clankit.ui.app import ClankitApp


def test_ui_build_and_render_frame():
    # Create a temporary repository with a commit and a dirty file
    tmp_dir = tempfile.mkdtemp(prefix="clankit_ui_smoke_")
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=tmp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Smoke User"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "smoke@example.com"], cwd=tmp_dir, check=True)

        with open(os.path.join(tmp_dir, "file.txt"), "w") as f:
            f.write("Line 1\n")
        subprocess.run(["git", "add", "file.txt"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_dir, check=True)

        # Create an unstaged change
        with open(os.path.join(tmp_dir, "file.txt"), "a") as f:
            f.write("Line 2 uncommitted\n")

        # Initialize ClankitApp with this test repo
        app = ClankitApp(initial_path=tmp_dir)
        app.build_ui()
        dpg.show_viewport()

        # Load initial repository state
        app.refresh()

        # Switch to history view and back to test view switching
        app._switch_view("history")
        app._switch_view("status")

        # Render 5 frames to ensure OpenGL pipeline and DPG loop operate smoothly
        for _ in range(5):
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

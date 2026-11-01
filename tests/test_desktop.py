"""Tests for Clankit desktop packaging, asset discovery, and .desktop installation."""

import os
import tempfile
from clankit.desktop import (
    get_asset_path,
    install_desktop_entry,
    uninstall_desktop_entry,
)


def test_asset_discovery():
    desktop_template = get_asset_path("clankit.desktop")
    svg_icon = get_asset_path("icons/clankit.svg")
    png_icon = get_asset_path("icons/clankit_256.png")

    assert os.path.isfile(desktop_template)
    assert os.path.isfile(svg_icon)
    assert os.path.isfile(png_icon)


def test_desktop_install_and_uninstall():
    tmp_data_dir = tempfile.mkdtemp(prefix="clankit_desktop_test_")
    try:
        old_xdg = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = tmp_data_dir

        # 1. Install
        success = install_desktop_entry(system_wide=False, executable_path="/custom/path/clankit")
        assert success is True

        desktop_file = os.path.join(tmp_data_dir, "applications", "clankit.desktop")
        assert os.path.isfile(desktop_file)

        with open(desktop_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Exec=/custom/path/clankit %F" in content
        assert "Icon=clankit" in content
        assert "Name=Clankit" in content
        assert "Categories=Development;RevisionControl;" in content

        # Check installed icons
        svg_installed = os.path.join(tmp_data_dir, "icons", "hicolor", "scalable", "apps", "clankit.svg")
        png_256_installed = os.path.join(tmp_data_dir, "icons", "hicolor", "256x256", "apps", "clankit.png")
        pixmap_installed = os.path.join(tmp_data_dir, "pixmaps", "clankit.png")

        assert os.path.isfile(svg_installed)
        assert os.path.isfile(png_256_installed)
        assert os.path.isfile(pixmap_installed)

        # 2. Uninstall
        uninstalled = uninstall_desktop_entry(system_wide=False)
        assert uninstalled is True
        assert not os.path.exists(desktop_file)
        assert not os.path.exists(svg_installed)
        assert not os.path.exists(png_256_installed)
        assert not os.path.exists(pixmap_installed)
    finally:
        if old_xdg is not None:
            os.environ["XDG_DATA_HOME"] = old_xdg
        else:
            os.environ.pop("XDG_DATA_HOME", None)

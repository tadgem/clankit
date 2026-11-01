"""Tests for Clankit theme system, ThemeManager, and dynamic color resolution."""

import os
import tempfile
import dearpygui.dearpygui as dpg
from clankit.ui.theme import (
    ThemeManager,
    THEME_SOURCETREE_DARK,
    THEME_SOURCETREE_LIGHT,
    THEME_GITHUB_DARK,
    THEME_NORD,
    THEME_SOLARIZED_DARK,
    SourceTreeColors,
    ThemeColors,
    get_theme_manager,
    apply_sourcetree_theme,
    create_primary_button_theme,
    create_danger_button_theme,
)


def test_theme_registration_and_list():
    mgr = ThemeManager()
    names = mgr.get_theme_names()
    assert "sourcetree_dark" in names
    assert "sourcetree_light" in names
    assert "github_dark" in names
    assert "nord" in names
    assert "solarized_dark" in names

    display_names = mgr.get_display_names()
    assert "SourceTree Dark" in display_names
    assert "SourceTree Light" in display_names
    assert "GitHub Dark" in display_names
    assert "Nord" in display_names
    assert "Solarized Dark" in display_names


def test_theme_persistence():
    tmp_config_dir = tempfile.mkdtemp(prefix="clankit_theme_test_")
    try:
        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = tmp_config_dir

        mgr = ThemeManager()
        # Default should be sourcetree_dark
        assert mgr.load_saved_theme_name() == "sourcetree_dark"

        # Save preference
        mgr.save_theme_preference("nord")
        assert mgr.load_saved_theme_name() == "nord"
    finally:
        if old_xdg is not None:
            os.environ["XDG_CONFIG_HOME"] = old_xdg
        else:
            os.environ.pop("XDG_CONFIG_HOME", None)


def test_theme_switching_and_dynamic_colors():
    dpg.create_context()
    try:
        mgr = get_theme_manager()
        # Apply dark theme
        mgr.apply_theme("sourcetree_dark", save_preference=False)
        assert SourceTreeColors.TEXT_NORMAL == THEME_SOURCETREE_DARK.text_normal
        assert SourceTreeColors.PRIMARY_BLUE == THEME_SOURCETREE_DARK.primary
        assert ThemeColors.STATUS_ADDED == THEME_SOURCETREE_DARK.status_added

        # Apply light theme
        mgr.apply_theme("sourcetree_light", save_preference=False)
        assert SourceTreeColors.TEXT_NORMAL == THEME_SOURCETREE_LIGHT.text_normal
        assert SourceTreeColors.PRIMARY_BLUE == THEME_SOURCETREE_LIGHT.primary
        assert ThemeColors.STATUS_ADDED == THEME_SOURCETREE_LIGHT.status_added

        # Apply GitHub Dark
        mgr.apply_theme("github_dark", save_preference=False)
        assert SourceTreeColors.TEXT_NORMAL == THEME_GITHUB_DARK.text_normal
        assert SourceTreeColors.PRIMARY_BLUE == THEME_GITHUB_DARK.primary

        # Apply Nord
        mgr.apply_theme("Nord", save_preference=False)
        assert SourceTreeColors.PRIMARY_BLUE == THEME_NORD.primary

        # Apply Solarized Dark
        mgr.apply_theme("solarized_dark", save_preference=False)
        assert SourceTreeColors.PRIMARY_BLUE == THEME_SOLARIZED_DARK.primary
    finally:
        # Reset back to dark theme
        mgr.apply_theme("sourcetree_dark", save_preference=False)
        dpg.destroy_context()


def test_button_themes_creation():
    dpg.create_context()
    try:
        p_theme = create_primary_button_theme()
        d_theme = create_danger_button_theme()
        assert dpg.does_item_exist(p_theme)
        assert dpg.does_item_exist(d_theme)

        # Re-applying theme should update existing theme items
        mgr = get_theme_manager()
        mgr.apply_theme("sourcetree_light", save_preference=False)
        assert dpg.does_item_exist(p_theme)
        assert dpg.does_item_exist(d_theme)
    finally:
        mgr.apply_theme("sourcetree_dark", save_preference=False)
        dpg.destroy_context()

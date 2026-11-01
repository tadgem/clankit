"""SourceTree-inspired theme and styling for Dear PyGui."""

from __future__ import annotations
import dearpygui.dearpygui as dpg


class SourceTreeColors:
    # Backgrounds
    BG_DARKEST = (24, 25, 28)
    BG_DARK = (32, 34, 37)
    BG_PANEL = (47, 49, 54)
    BG_ROW_ALT = (40, 42, 46)

    # Borders & Accents
    BORDER = (54, 57, 63)
    PRIMARY_BLUE = (38, 132, 255)
    PRIMARY_HOVER = (60, 150, 255)
    ACCENT_PURPLE = (88, 101, 242)

    # Text
    TEXT_NORMAL = (220, 221, 222)
    TEXT_MUTED = (142, 146, 151)
    TEXT_WHITE = (255, 255, 255)

    # Git Status
    STATUS_MODIFIED = (240, 178, 50)
    STATUS_ADDED = (63, 185, 80)
    STATUS_DELETED = (248, 81, 73)
    STATUS_UNTRACKED = (163, 113, 247)
    STATUS_CONFLICT = (255, 123, 114)

    # Diff
    DIFF_ADD_TEXT = (80, 220, 120)
    DIFF_ADD_BG = (22, 60, 35, 200)
    DIFF_DEL_TEXT = (255, 100, 100)
    DIFF_DEL_BG = (75, 25, 30, 200)
    DIFF_HEADER_TEXT = (88, 166, 255)
    DIFF_HEADER_BG = (30, 45, 65, 200)
    DIFF_META_TEXT = (160, 165, 175)


def apply_sourcetree_theme() -> int:
    """Creates and applies the SourceTree dark theme to Dear PyGui."""
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvAll):
            # Window & Panels
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, SourceTreeColors.BG_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, SourceTreeColors.BG_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, SourceTreeColors.BG_DARKEST)
            dpg.add_theme_color(dpg.mvThemeCol_Border, SourceTreeColors.BORDER)

            # Headers & Trees
            dpg.add_theme_color(dpg.mvThemeCol_Header, SourceTreeColors.BG_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (64, 68, 75))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, SourceTreeColors.PRIMARY_BLUE)

            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (64, 68, 75))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (79, 84, 92))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, SourceTreeColors.PRIMARY_BLUE)

            # Inputs & Frames
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, SourceTreeColors.BG_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (47, 49, 54))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (58, 62, 68))

            # Tabs
            dpg.add_theme_color(dpg.mvThemeCol_Tab, SourceTreeColors.BG_PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (64, 68, 75))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, SourceTreeColors.PRIMARY_BLUE)

            # Tables
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, SourceTreeColors.BG_DARKEST)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, SourceTreeColors.BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, SourceTreeColors.BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, SourceTreeColors.BG_ROW_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, SourceTreeColors.BG_PANEL)

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, SourceTreeColors.TEXT_NORMAL)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, SourceTreeColors.TEXT_MUTED)

            # Scrollbars
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, SourceTreeColors.BG_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (64, 68, 75))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (79, 84, 92))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, SourceTreeColors.PRIMARY_BLUE)

            # Styles
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)

    dpg.bind_theme(theme_id)
    return theme_id


def create_primary_button_theme() -> int:
    """Theme for primary CTA buttons like Commit or Push."""
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 102, 204))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (38, 132, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 82, 163))
            dpg.add_theme_color(dpg.mvThemeCol_Text, SourceTreeColors.TEXT_WHITE)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
    return theme_id


def create_danger_button_theme() -> int:
    """Theme for destructive buttons like Discard or Delete Branch."""
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 40, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (220, 53, 69))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (140, 30, 40))
            dpg.add_theme_color(dpg.mvThemeCol_Text, SourceTreeColors.TEXT_WHITE)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
    return theme_id

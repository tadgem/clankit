"""Multi-theme styling system for Clankit with dynamic runtime switching."""

from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import dearpygui.dearpygui as dpg

ColorTuple = Tuple[int, ...]


@dataclass
class ThemePalette:
    name: str
    display_name: str
    is_dark: bool

    # Backgrounds
    bg_window: ColorTuple
    bg_child: ColorTuple
    bg_popup: ColorTuple
    bg_row_alt: ColorTuple

    # Borders & Controls
    border: ColorTuple
    header_hover: ColorTuple
    button: ColorTuple
    button_hover: ColorTuple
    frame: ColorTuple
    frame_hover: ColorTuple
    frame_active: ColorTuple

    # Accents & Brand
    primary: ColorTuple
    primary_hover: ColorTuple
    accent_purple: ColorTuple

    # Text
    text_normal: ColorTuple
    text_muted: ColorTuple
    text_white: ColorTuple

    # Git Status
    status_modified: ColorTuple
    status_added: ColorTuple
    status_deleted: ColorTuple
    status_untracked: ColorTuple
    status_conflict: ColorTuple

    # Diff Syntax Highlighting
    diff_add_text: ColorTuple
    diff_add_bg: ColorTuple
    diff_del_text: ColorTuple
    diff_del_bg: ColorTuple
    diff_header_text: ColorTuple
    diff_header_bg: ColorTuple
    diff_meta_text: ColorTuple

    # Button themes
    primary_button: ColorTuple
    primary_button_hover: ColorTuple
    primary_button_active: ColorTuple
    danger_button: ColorTuple
    danger_button_hover: ColorTuple
    danger_button_active: ColorTuple


# ---------------- Built-in Themes ----------------

THEME_SOURCETREE_DARK = ThemePalette(
    name="sourcetree_dark",
    display_name="SourceTree Dark",
    is_dark=True,
    bg_window=(32, 34, 37),
    bg_child=(47, 49, 54),
    bg_popup=(24, 25, 28),
    bg_row_alt=(40, 42, 46),
    border=(54, 57, 63),
    header_hover=(64, 68, 75),
    button=(64, 68, 75),
    button_hover=(79, 84, 92),
    frame=(32, 34, 37),
    frame_hover=(47, 49, 54),
    frame_active=(58, 62, 68),
    primary=(38, 132, 255),
    primary_hover=(60, 150, 255),
    accent_purple=(88, 101, 242),
    text_normal=(220, 221, 222),
    text_muted=(142, 146, 151),
    text_white=(255, 255, 255),
    status_modified=(240, 178, 50),
    status_added=(63, 185, 80),
    status_deleted=(248, 81, 73),
    status_untracked=(163, 113, 247),
    status_conflict=(255, 123, 114),
    diff_add_text=(80, 220, 120),
    diff_add_bg=(22, 60, 35, 200),
    diff_del_text=(255, 100, 100),
    diff_del_bg=(75, 25, 30, 200),
    diff_header_text=(88, 166, 255),
    diff_header_bg=(30, 45, 65, 200),
    diff_meta_text=(160, 165, 175),
    primary_button=(0, 102, 204),
    primary_button_hover=(38, 132, 255),
    primary_button_active=(0, 82, 163),
    danger_button=(180, 40, 50),
    danger_button_hover=(220, 53, 69),
    danger_button_active=(140, 30, 40),
)

THEME_SOURCETREE_LIGHT = ThemePalette(
    name="sourcetree_light",
    display_name="SourceTree Light",
    is_dark=False,
    bg_window=(244, 245, 247),
    bg_child=(255, 255, 255),
    bg_popup=(255, 255, 255),
    bg_row_alt=(244, 245, 247),
    border=(220, 224, 230),
    header_hover=(235, 237, 240),
    button=(235, 237, 240),
    button_hover=(220, 224, 230),
    frame=(255, 255, 255),
    frame_hover=(240, 242, 245),
    frame_active=(230, 233, 238),
    primary=(0, 82, 204),
    primary_hover=(38, 132, 255),
    accent_purple=(101, 84, 192),
    text_normal=(23, 43, 77),
    text_muted=(107, 119, 140),
    text_white=(255, 255, 255),
    status_modified=(217, 119, 6),
    status_added=(16, 149, 93),
    status_deleted=(220, 38, 38),
    status_untracked=(124, 58, 237),
    status_conflict=(220, 38, 38),
    diff_add_text=(16, 149, 93),
    diff_add_bg=(227, 252, 239, 200),
    diff_del_text=(220, 38, 38),
    diff_del_bg=(254, 226, 226, 200),
    diff_header_text=(2, 106, 167),
    diff_header_bg=(222, 235, 255, 200),
    diff_meta_text=(107, 119, 140),
    primary_button=(0, 82, 204),
    primary_button_hover=(38, 132, 255),
    primary_button_active=(0, 65, 160),
    danger_button=(220, 38, 38),
    danger_button_hover=(239, 68, 68),
    danger_button_active=(185, 28, 28),
)

THEME_GITHUB_DARK = ThemePalette(
    name="github_dark",
    display_name="GitHub Dark",
    is_dark=True,
    bg_window=(13, 17, 23),
    bg_child=(22, 27, 34),
    bg_popup=(22, 27, 34),
    bg_row_alt=(26, 31, 39),
    border=(48, 54, 61),
    header_hover=(48, 54, 61),
    button=(33, 38, 45),
    button_hover=(48, 54, 61),
    frame=(13, 17, 23),
    frame_hover=(33, 38, 45),
    frame_active=(48, 54, 61),
    primary=(88, 166, 255),
    primary_hover=(121, 192, 255),
    accent_purple=(188, 140, 255),
    text_normal=(201, 209, 217),
    text_muted=(139, 148, 158),
    text_white=(240, 246, 252),
    status_modified=(210, 153, 34),
    status_added=(63, 185, 80),
    status_deleted=(248, 81, 73),
    status_untracked=(163, 113, 247),
    status_conflict=(248, 81, 73),
    diff_add_text=(63, 185, 80),
    diff_add_bg=(22, 60, 35, 200),
    diff_del_text=(248, 81, 73),
    diff_del_bg=(75, 25, 30, 200),
    diff_header_text=(88, 166, 255),
    diff_header_bg=(30, 45, 65, 200),
    diff_meta_text=(139, 148, 158),
    primary_button=(31, 111, 235),
    primary_button_hover=(56, 139, 253),
    primary_button_active=(24, 88, 186),
    danger_button=(218, 54, 51),
    danger_button_hover=(248, 81, 73),
    danger_button_active=(164, 14, 14),
)

THEME_NORD = ThemePalette(
    name="nord",
    display_name="Nord",
    is_dark=True,
    bg_window=(46, 52, 64),
    bg_child=(59, 66, 82),
    bg_popup=(46, 52, 64),
    bg_row_alt=(53, 59, 74),
    border=(67, 76, 94),
    header_hover=(67, 76, 94),
    button=(67, 76, 94),
    button_hover=(76, 86, 106),
    frame=(46, 52, 64),
    frame_hover=(59, 66, 82),
    frame_active=(67, 76, 94),
    primary=(136, 192, 208),
    primary_hover=(129, 161, 193),
    accent_purple=(180, 142, 173),
    text_normal=(236, 239, 244),
    text_muted=(216, 222, 233),
    text_white=(255, 255, 255),
    status_modified=(235, 203, 139),
    status_added=(163, 190, 140),
    status_deleted=(191, 97, 106),
    status_untracked=(180, 142, 173),
    status_conflict=(191, 97, 106),
    diff_add_text=(163, 190, 140),
    diff_add_bg=(40, 60, 48, 200),
    diff_del_text=(191, 97, 106),
    diff_del_bg=(70, 35, 40, 200),
    diff_header_text=(136, 192, 208),
    diff_header_bg=(45, 60, 75, 200),
    diff_meta_text=(147, 156, 170),
    primary_button=(94, 129, 172),
    primary_button_hover=(129, 161, 193),
    primary_button_active=(76, 106, 143),
    danger_button=(191, 97, 106),
    danger_button_hover=(208, 135, 112),
    danger_button_active=(160, 75, 84),
)

THEME_SOLARIZED_DARK = ThemePalette(
    name="solarized_dark",
    display_name="Solarized Dark",
    is_dark=True,
    bg_window=(0, 43, 54),
    bg_child=(7, 54, 66),
    bg_popup=(0, 43, 54),
    bg_row_alt=(5, 48, 59),
    border=(88, 110, 117),
    header_hover=(14, 68, 82),
    button=(14, 68, 82),
    button_hover=(20, 80, 96),
    frame=(0, 43, 54),
    frame_hover=(7, 54, 66),
    frame_active=(14, 68, 82),
    primary=(38, 139, 210),
    primary_hover=(42, 161, 152),
    accent_purple=(108, 113, 196),
    text_normal=(131, 148, 150),
    text_muted=(88, 110, 117),
    text_white=(253, 246, 227),
    status_modified=(181, 137, 0),
    status_added=(133, 153, 0),
    status_deleted=(220, 50, 47),
    status_untracked=(108, 113, 196),
    status_conflict=(220, 50, 47),
    diff_add_text=(133, 153, 0),
    diff_add_bg=(20, 60, 30, 200),
    diff_del_text=(220, 50, 47),
    diff_del_bg=(70, 25, 25, 200),
    diff_header_text=(38, 139, 210),
    diff_header_bg=(20, 50, 70, 200),
    diff_meta_text=(101, 123, 131),
    primary_button=(38, 139, 210),
    primary_button_hover=(42, 161, 152),
    primary_button_active=(30, 110, 166),
    danger_button=(220, 50, 47),
    danger_button_hover=(203, 75, 22),
    danger_button_active=(170, 35, 33),
)


PRIMARY_BTN_THEME_TAG = "clankit_primary_btn_theme"
DANGER_BTN_THEME_TAG = "clankit_danger_btn_theme"
GLOBAL_THEME_TAG = "clankit_global_theme"


class ThemeManager:
    """Coordinates available themes, application theming, and user preferences."""

    CONFIG_FILE_NAME = "config.json"

    def __init__(self) -> None:
        self.themes: Dict[str, ThemePalette] = {
            THEME_SOURCETREE_DARK.name: THEME_SOURCETREE_DARK,
            THEME_SOURCETREE_LIGHT.name: THEME_SOURCETREE_LIGHT,
            THEME_GITHUB_DARK.name: THEME_GITHUB_DARK,
            THEME_NORD.name: THEME_NORD,
            THEME_SOLARIZED_DARK.name: THEME_SOLARIZED_DARK,
        }
        self.current_theme: ThemePalette = THEME_SOURCETREE_DARK
        self.global_theme_id: Optional[str] = None

    def get_theme_list(self) -> List[Tuple[str, str]]:
        """Return list of (theme_name, display_name)."""
        return [(p.name, p.display_name) for p in self.themes.values()]

    def get_theme_names(self) -> List[str]:
        return list(self.themes.keys())

    def get_display_names(self) -> List[str]:
        return [p.display_name for p in self.themes.values()]

    def get_theme_by_display_name(self, display_name: str) -> Optional[ThemePalette]:
        for p in self.themes.values():
            if p.display_name == display_name:
                return p
        return None

    def get_config_path(self) -> str:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        return os.path.join(base, "clankit", self.CONFIG_FILE_NAME)

    def load_saved_theme_name(self) -> str:
        config_path = self.get_config_path()
        if os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    theme_name = data.get("theme")
                    if theme_name in self.themes:
                        return theme_name
            except Exception:
                pass
        return THEME_SOURCETREE_DARK.name

    def save_theme_preference(self, theme_name: str) -> None:
        config_path = self.get_config_path()
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            data = {}
            if os.path.isfile(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["theme"] = theme_name
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def apply_theme(self, theme_key_or_display: str, save_preference: bool = True) -> str:
        """Apply theme to Dear PyGui and update button themes."""
        palette = self.themes.get(theme_key_or_display)
        if not palette:
            palette = self.get_theme_by_display_name(theme_key_or_display)
        if not palette:
            palette = THEME_SOURCETREE_DARK

        self.current_theme = palette
        if save_preference:
            self.save_theme_preference(palette.name)

        # Build Dear PyGui Global Theme
        if not dpg.does_item_exist(GLOBAL_THEME_TAG):
            dpg.add_theme(tag=GLOBAL_THEME_TAG)
        else:
            dpg.delete_item(GLOBAL_THEME_TAG, children_only=True)

        with dpg.theme_component(dpg.mvAll, parent=GLOBAL_THEME_TAG):
            # Window & Panels
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, palette.bg_window)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, palette.bg_child)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, palette.bg_popup)
            dpg.add_theme_color(dpg.mvThemeCol_Border, palette.border)

            # Headers & Trees
            dpg.add_theme_color(dpg.mvThemeCol_Header, palette.bg_child)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, palette.header_hover)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, palette.primary)

            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, palette.button)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, palette.button_hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, palette.primary)

            # Inputs & Frames
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, palette.frame)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, palette.frame_hover)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, palette.frame_active)

            # Tabs
            dpg.add_theme_color(dpg.mvThemeCol_Tab, palette.bg_child)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, palette.header_hover)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, palette.primary)

            # Tables
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, palette.bg_popup)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, palette.border)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, palette.border)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, palette.bg_row_alt)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, palette.bg_child)

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, palette.text_normal)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, palette.text_muted)

            # Scrollbars
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, palette.bg_window)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, palette.button)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, palette.button_hover)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, palette.primary)

            # Styles
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)

        dpg.bind_theme(GLOBAL_THEME_TAG)
        self.global_theme_id = GLOBAL_THEME_TAG

        # Update primary & danger button themes
        self._update_button_themes(palette)
        return GLOBAL_THEME_TAG

    def _update_button_themes(self, palette: ThemePalette) -> None:
        """Create or update button theme components in place."""
        if not dpg.does_item_exist(PRIMARY_BTN_THEME_TAG):
            dpg.add_theme(tag=PRIMARY_BTN_THEME_TAG)
        else:
            dpg.delete_item(PRIMARY_BTN_THEME_TAG, children_only=True)

        with dpg.theme_component(dpg.mvButton, parent=PRIMARY_BTN_THEME_TAG):
            dpg.add_theme_color(dpg.mvThemeCol_Button, palette.primary_button)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, palette.primary_button_hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, palette.primary_button_active)
            dpg.add_theme_color(dpg.mvThemeCol_Text, palette.text_white)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)

        if not dpg.does_item_exist(DANGER_BTN_THEME_TAG):
            dpg.add_theme(tag=DANGER_BTN_THEME_TAG)
        else:
            dpg.delete_item(DANGER_BTN_THEME_TAG, children_only=True)

        with dpg.theme_component(dpg.mvButton, parent=DANGER_BTN_THEME_TAG):
            dpg.add_theme_color(dpg.mvThemeCol_Button, palette.danger_button)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, palette.danger_button_hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, palette.danger_button_active)
            dpg.add_theme_color(dpg.mvThemeCol_Text, palette.text_white)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)


# Global ThemeManager singleton
_theme_manager = ThemeManager()


def get_theme_manager() -> ThemeManager:
    return _theme_manager


class _DynamicThemeColorsMeta(type):
    """Metaclass mapping uppercase color attributes to the currently active ThemePalette."""

    def __getattr__(cls, name: str) -> ColorTuple:
        palette = _theme_manager.current_theme
        attr_map = {
            "BG_DARKEST": palette.bg_popup,
            "BG_DARK": palette.bg_window,
            "BG_PANEL": palette.bg_child,
            "BG_ROW_ALT": palette.bg_row_alt,
            "BORDER": palette.border,
            "PRIMARY_BLUE": palette.primary,
            "PRIMARY_HOVER": palette.primary_hover,
            "ACCENT_PURPLE": palette.accent_purple,
            "TEXT_NORMAL": palette.text_normal,
            "TEXT_MUTED": palette.text_muted,
            "TEXT_WHITE": palette.text_white,
            "STATUS_MODIFIED": palette.status_modified,
            "STATUS_ADDED": palette.status_added,
            "STATUS_DELETED": palette.status_deleted,
            "STATUS_UNTRACKED": palette.status_untracked,
            "STATUS_CONFLICT": palette.status_conflict,
            "DIFF_ADD_TEXT": palette.diff_add_text,
            "DIFF_ADD_BG": palette.diff_add_bg,
            "DIFF_DEL_TEXT": palette.diff_del_text,
            "DIFF_DEL_BG": palette.diff_del_bg,
            "DIFF_HEADER_TEXT": palette.diff_header_text,
            "DIFF_HEADER_BG": palette.diff_header_bg,
            "DIFF_META_TEXT": palette.diff_meta_text,
        }
        if name in attr_map:
            return attr_map[name]
        lower_name = name.lower()
        if hasattr(palette, lower_name):
            return getattr(palette, lower_name)
        raise AttributeError(f"ThemePalette has no color attribute '{name}'")


class SourceTreeColors(metaclass=_DynamicThemeColorsMeta):
    """Dynamically reflects colors of the active theme for backwards compatibility."""
    pass


class ThemeColors(metaclass=_DynamicThemeColorsMeta):
    """Alias for active theme colors."""
    pass


def apply_sourcetree_theme() -> int:
    """Apply the saved or default theme on startup."""
    saved = _theme_manager.load_saved_theme_name()
    return _theme_manager.apply_theme(saved, save_preference=False)


def create_primary_button_theme() -> str:
    """Return the active primary CTA button theme tag."""
    if not dpg.does_item_exist(PRIMARY_BTN_THEME_TAG):
        _theme_manager._update_button_themes(_theme_manager.current_theme)
    return PRIMARY_BTN_THEME_TAG


def create_danger_button_theme() -> str:
    """Return the active destructive button theme tag."""
    if not dpg.does_item_exist(DANGER_BTN_THEME_TAG):
        _theme_manager._update_button_themes(_theme_manager.current_theme)
    return DANGER_BTN_THEME_TAG

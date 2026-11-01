"""Font management and typography for Dear PyGui in Clankit."""

from __future__ import annotations
import os
import sys
from typing import Optional, Tuple
import dearpygui.dearpygui as dpg
from clankit.desktop import get_asset_path


class FontManager:
    """Manages application fonts, font registries, and item font binding."""

    def __init__(self) -> None:
        self.main_font: Optional[int] = None
        self.mono_font: Optional[int] = None
        self.registry_tag: str = "clankit_font_registry"

    def _find_font_file(self, bundled_name: str, system_candidates: list[str]) -> Optional[str]:
        # 1. Bundled font asset
        bundled = get_asset_path(f"fonts/{bundled_name}")
        if os.path.isfile(bundled):
            return bundled

        # 2. System paths
        for path in system_candidates:
            expanded = os.path.expanduser(path)
            if os.path.isfile(expanded):
                return expanded

        return None

    def setup_fonts(self, ui_size: int = 15, mono_size: int = 14) -> Tuple[Optional[int], Optional[int]]:
        """Load and register the application UI font and monospace code font."""
        if dpg.does_item_exist(self.registry_tag):
            return (self.main_font, self.mono_font)

        ui_candidates = [
            "/usr/share/fonts/TTF/OpenSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/cantarell/Cantarell-VF.otf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/SFProText-Regular.otf",
            "/Library/Fonts/Arial.ttf",
        ]

        mono_candidates = [
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/Adwaita/AdwaitaMono-Regular.ttf",
            "/usr/share/fonts/TTF/FiraMono-Regular.ttf",
            "/usr/share/fonts/TTF/Hack-Regular.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
            "C:\\Windows\\Fonts\\cascadiacode.ttf",
            "/System/Library/Fonts/SFMono-Regular.otf",
            "/Library/Fonts/Courier New.ttf",
        ]

        main_font_path = self._find_font_file("OpenSans-Regular.ttf", ui_candidates)
        mono_font_path = self._find_font_file("DejaVuSansMono.ttf", mono_candidates)

        try:
            with dpg.font_registry(tag=self.registry_tag):
                if main_font_path and os.path.exists(main_font_path):
                    self.main_font = dpg.add_font(main_font_path, ui_size)
                if mono_font_path and os.path.exists(mono_font_path):
                    self.mono_font = dpg.add_font(mono_font_path, mono_size)

            if self.main_font is not None:
                dpg.bind_font(self.main_font)
        except Exception:
            # Fall back safely to Dear PyGui's default font if font loading fails
            pass

        return (self.main_font, self.mono_font)

    def bind_mono_font(self, item_tag: str | int) -> None:
        """Bind monospace font to a specific item (e.g. diff viewer, console)."""
        if self.mono_font is not None and dpg.does_item_exist(item_tag):
            try:
                dpg.bind_item_font(item_tag, self.mono_font)
            except Exception:
                pass

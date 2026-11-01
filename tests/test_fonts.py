"""Tests for font discovery, bundled font assets, and font manager."""

import os
import dearpygui.dearpygui as dpg
from clankit.desktop import get_asset_path
from clankit.ui.font_manager import FontManager


def test_bundled_fonts_exist():
    regular_font = get_asset_path("fonts/OpenSans-Regular.ttf")
    semibold_font = get_asset_path("fonts/OpenSans-SemiBold.ttf")
    mono_font = get_asset_path("fonts/DejaVuSansMono.ttf")

    assert os.path.isfile(regular_font), f"Missing bundled font: {regular_font}"
    assert os.path.isfile(semibold_font), f"Missing bundled font: {semibold_font}"
    assert os.path.isfile(mono_font), f"Missing bundled font: {mono_font}"

    # Verify font files have non-zero size
    assert os.path.getsize(regular_font) > 50000
    assert os.path.getsize(mono_font) > 50000


def test_font_manager_setup():
    dpg.create_context()
    try:
        fm = FontManager()
        main_font, mono_font = fm.setup_fonts(ui_size=15, mono_size=14)

        assert main_font is not None
        assert mono_font is not None
        assert dpg.does_item_exist(main_font)
        assert dpg.does_item_exist(mono_font)

        # Calling setup_fonts a second time should return existing registered fonts
        main_font2, mono_font2 = fm.setup_fonts()
        assert main_font2 == main_font
        assert mono_font2 == mono_font

        # Test binding mono font to an item
        with dpg.window(label="TestWin", tag="test_win"):
            text_item = dpg.add_text("diff line", tag="diff_text_tag")

        fm.bind_mono_font("diff_text_tag")
        # Should not throw on non-existent item
        fm.bind_mono_font("non_existent_item_tag")
    finally:
        dpg.destroy_context()

"""Desktop integration utilities for Clankit on Linux and XDG desktop environments."""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
from importlib import resources
from typing import Optional


def get_asset_path(subpath: str) -> str:
    """Return the filesystem path for a bundled asset."""
    try:
        res = resources.files("clankit").joinpath("assets", subpath)
        return str(res)
    except Exception:
        fallback = os.path.join(os.path.dirname(__file__), "assets", subpath)
        return fallback


def install_desktop_entry(system_wide: bool = False, executable_path: Optional[str] = None) -> bool:
    """Install .desktop entry and icons for system application launcher integration."""
    if system_wide:
        apps_dir = "/usr/share/applications"
        icons_base = "/usr/share/icons/hicolor"
        pixmaps_dir = "/usr/share/pixmaps"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        apps_dir = os.path.join(xdg_data, "applications")
        icons_base = os.path.join(xdg_data, "icons", "hicolor")
        pixmaps_dir = os.path.join(xdg_data, "pixmaps")

    os.makedirs(apps_dir, exist_ok=True)
    os.makedirs(pixmaps_dir, exist_ok=True)

    # 1. Install icons
    icon_svg = get_asset_path("icons/clankit.svg")
    icon_png_256 = get_asset_path("icons/clankit_256.png")
    if not os.path.exists(icon_png_256):
        icon_png_256 = get_asset_path("icons/clankit.png")

    # Install scalable SVG
    if os.path.exists(icon_svg):
        svg_target_dir = os.path.join(icons_base, "scalable", "apps")
        os.makedirs(svg_target_dir, exist_ok=True)
        shutil.copy2(icon_svg, os.path.join(svg_target_dir, "clankit.svg"))

    # Install PNGs across standard hicolor resolutions
    sizes = [16, 32, 48, 64, 128, 256, 512]
    for size in sizes:
        src_png = get_asset_path(f"icons/clankit_{size}.png")
        if os.path.exists(src_png):
            png_target_dir = os.path.join(icons_base, f"{size}x{size}", "apps")
            os.makedirs(png_target_dir, exist_ok=True)
            shutil.copy2(src_png, os.path.join(png_target_dir, "clankit.png"))

    # Copy to pixmaps for legacy desktop managers
    if os.path.exists(icon_png_256):
        shutil.copy2(icon_png_256, os.path.join(pixmaps_dir, "clankit.png"))

    # 2. Determine Exec path
    if not executable_path:
        # Check if 'clankit' is in system PATH
        clankit_bin = shutil.which("clankit")
        if clankit_bin:
            exec_cmd = f"{clankit_bin} %F"
        else:
            # Fall back to python executable running clankit module
            exec_cmd = f"{sys.executable} -m clankit.main %F"
    else:
        exec_cmd = f"{executable_path} %F"

    # 3. Create .desktop file
    desktop_template = get_asset_path("clankit.desktop")
    dest_desktop = os.path.join(apps_dir, "clankit.desktop")

    if os.path.exists(desktop_template):
        with open(desktop_template, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = (
            "[Desktop Entry]\n"
            "Version=1.0\n"
            "Type=Application\n"
            "Name=Clankit\n"
            "GenericName=Git GUI Client\n"
            "Comment=A fast, SourceTree-like Git GUI client powered by Dear PyGui\n"
            "Exec=clankit %F\n"
            "Icon=clankit\n"
            "Terminal=false\n"
            "Categories=Development;RevisionControl;\n"
            "StartupWMClass=clankit\n"
            "Keywords=git;version-control;sourcetree;diff;commit;gui;\n"
            "MimeType=inode/directory;\n"
        )

    # Replace Exec line with exact resolved command
    lines = []
    for line in content.splitlines():
        if line.startswith("Exec="):
            lines.append(f"Exec={exec_cmd}")
        else:
            lines.append(line)
    final_content = "\n".join(lines) + "\n"

    with open(dest_desktop, "w", encoding="utf-8") as f:
        f.write(final_content)

    try:
        os.chmod(dest_desktop, 0o755)
    except Exception:
        pass

    # 4. Update desktop and icon databases if available
    try:
        subprocess.run(["update-desktop-database", apps_dir], check=False, capture_output=True)
    except Exception:
        pass

    try:
        subprocess.run(["gtk-update-icon-cache", "-f", "-t", icons_base], check=False, capture_output=True)
    except Exception:
        pass

    print(f"✓ Clankit desktop entry successfully installed to: {dest_desktop}")
    print(f"✓ Application launcher icon installed to: {icons_base}")
    print("  Clankit is now available in your desktop application menu / launcher.")
    return True


def uninstall_desktop_entry(system_wide: bool = False) -> bool:
    """Remove installed .desktop entry and icons."""
    if system_wide:
        apps_dir = "/usr/share/applications"
        icons_base = "/usr/share/icons/hicolor"
        pixmaps_dir = "/usr/share/pixmaps"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        apps_dir = os.path.join(xdg_data, "applications")
        icons_base = os.path.join(xdg_data, "icons", "hicolor")
        pixmaps_dir = os.path.join(xdg_data, "pixmaps")

    desktop_file = os.path.join(apps_dir, "clankit.desktop")
    if os.path.exists(desktop_file):
        os.remove(desktop_file)
        print(f"✓ Removed: {desktop_file}")

    pixmap_file = os.path.join(pixmaps_dir, "clankit.png")
    if os.path.exists(pixmap_file):
        os.remove(pixmap_file)

    svg_file = os.path.join(icons_base, "scalable", "apps", "clankit.svg")
    if os.path.exists(svg_file):
        os.remove(svg_file)

    sizes = [16, 32, 48, 64, 128, 256, 512]
    for size in sizes:
        png_file = os.path.join(icons_base, f"{size}x{size}", "apps", "clankit.png")
        if os.path.exists(png_file):
            os.remove(png_file)

    try:
        subprocess.run(["update-desktop-database", apps_dir], check=False, capture_output=True)
    except Exception:
        pass

    print("✓ Clankit desktop integration uninstalled.")
    return True


def main() -> int:
    """CLI handler for desktop install/uninstall."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="clankit-desktop",
        description="Install or uninstall Clankit desktop launcher and application icons.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["install", "uninstall"],
        default="install",
        help="Action to perform (default: install)",
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Install/uninstall system-wide into /usr/share (requires root)",
    )

    args = parser.parse_args()
    if args.action == "uninstall":
        uninstall_desktop_entry(system_wide=args.system)
    else:
        install_desktop_entry(system_wide=args.system)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line entry point for Clankit."""

from __future__ import annotations
import argparse
import os
import sys
from clankit.ui.app import ClankitApp


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="clankit",
        description="A fast, unbiased SourceTree-like Git GUI wrapper in Python powered by Dear PyGui.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        help="Path to the Git repository (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show Clankit version and exit",
    )
    parser.add_argument(
        "--install-desktop",
        action="store_true",
        help="Install desktop launcher (.desktop) and application icons for system menu integration",
    )
    parser.add_argument(
        "--uninstall-desktop",
        action="store_true",
        help="Uninstall system desktop launcher and application icons",
    )
    parser.add_argument(
        "--theme",
        dest="theme",
        default=None,
        help="Initial theme to use ('SourceTree Dark', 'SourceTree Light', 'GitHub Dark', 'Nord', 'Solarized Dark')",
    )

    args = parser.parse_args()

    if args.install_desktop:
        from clankit.desktop import install_desktop_entry
        return 0 if install_desktop_entry() else 1

    if args.uninstall_desktop:
        from clankit.desktop import uninstall_desktop_entry
        return 0 if uninstall_desktop_entry() else 1

    if args.theme:
        from clankit.ui.theme import get_theme_manager
        get_theme_manager().apply_theme(args.theme, save_preference=False)

    app = ClankitApp(initial_path=args.path)
    try:
        app.run()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        sys.stderr.write(f"Clankit encountered a fatal error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

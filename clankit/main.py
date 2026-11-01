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

    args = parser.parse_args()

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

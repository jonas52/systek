from __future__ import annotations

import argparse

from .app import SystekApp
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="systek", description="Linux admin TUI")
    parser.add_argument("--version", action="store_true", help="Affiche la version")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(__version__)
        return
    app = SystekApp()
    app.run()


if __name__ == "__main__":
    main()

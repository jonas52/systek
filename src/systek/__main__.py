from __future__ import annotations

import argparse

from .app import SystekApp
from .permissions import is_root
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="systek", description="Linux admin console")
    parser.add_argument("--version", action="store_true", help="Afficher la version")
    parser.add_argument("--doctor", action="store_true", help="Afficher un diagnostic rapide")
    parser.add_argument("--update", action="store_true", help="Afficher la procédure de mise à jour")
    parser.add_argument("--uninstall", action="store_true", help="Afficher la procédure de désinstallation")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.version:
        print(__version__)
        return

    if args.doctor:
        print(f"Systek {__version__}")
        print(f"Mode root : {'oui' if is_root() else 'non'}")
        return

    if args.update:
        print("Commande recommandée : sudo systek puis action 'Mettre à jour Systek'")
        return

    if args.uninstall:
        print("Commande recommandée : sudo /opt/systek/uninstall.sh")
        return

    app = SystekApp()
    app.run()


if __name__ == "__main__":
    main()

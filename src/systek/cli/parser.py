import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="systek", description="Linux system administration TUI")
    parser.add_argument("--update", action="store_true", help="Met à jour Systek")
    parser.add_argument("--uninstall", action="store_true", help="Désinstalle Systek")
    parser.add_argument("--doctor", action="store_true", help="Diagnostic installation")
    parser.add_argument("--readonly", action="store_true", help="Force le mode lecture seule")
    parser.add_argument("--version", action="store_true", help="Affiche la version")
    return parser

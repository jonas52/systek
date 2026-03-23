from .cli.parser import build_parser
from .version import __version__
from .core.updater import update_systek
from .app import SystekApp
from .permissions import is_root


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if args.update:
        pull, pip_sync, editable = update_systek()
        print(pull.stdout or "Update git OK")
        print(pip_sync.stdout or "Dependencies OK")
        print(editable.stdout or "Editable install OK")
        return

    if args.uninstall:
        print("Utilise : sudo /opt/systek/uninstall.sh")
        return

    if args.doctor:
        print(f"Systek {__version__}")
        print(f"Mode root : {'oui' if is_root() else 'non'}")
        print("Commande recommandée : sudo systek")
        return

    app = SystekApp(readonly=args.readonly)
    app.run()


if __name__ == "__main__":
    main()

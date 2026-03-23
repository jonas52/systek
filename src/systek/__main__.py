from .app import SystekApp
from .cli.parser import build_parser
from .core.updater import update_systek
from .permissions import is_root
from .version import __version__


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if args.update:
        pull, pip_sync, editable = update_systek()
        print(pull.stdout or pull.stderr or "Git OK")
        print(pip_sync.stdout or pip_sync.stderr or "Deps OK")
        print(editable.stdout or editable.stderr or "Editable OK")
        return

    if args.uninstall:
        print("Utilise : sudo /opt/systek/uninstall.sh")
        return

    if args.doctor:
        print(f"Systek {__version__}")
        print(f"Mode root : {'oui' if is_root() else 'non'}")
        print("Commande recommandée : sudo systek")
        return

    SystekApp(readonly=args.readonly).run()


if __name__ == "__main__":
    main()

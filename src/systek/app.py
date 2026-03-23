from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label

from .permissions import is_root
from .core.packages import detect_package_manager
from .core.system import get_os_name, get_kernel, get_hostname
from .core.network import get_local_ips
from .core.monitor import cpu_percent, ram_percent, disk_percent, load_average, uptime_seconds, network_counters, cpu_temperature
from .version import __version__


CATEGORIES = [
    ("system", "Système", "Mises à jour, reboot, arrêt."),
    ("packages", "Paquets", "Installer, supprimer, rechercher, hold/unhold."),
    ("services", "Services", "Lister, surveiller, démarrer, arrêter, activer."),
    ("monitor", "Surveillance", "CPU, RAM, disque, réseau, température."),
    ("disks", "Disques", "Lister et monter des disques."),
    ("network", "Réseau", "IP, interfaces, connectivité."),
    ("firewall", "Pare-feu", "UFW, règles et état."),
    ("logs", "Logs", "Logs système et services."),
    ("tools", "Outils", "Cockpit, doctor et outils utiles."),
    ("systek", "Systek", "Update, uninstall, version."),
]


class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    TITLE = "Systek"
    SUB_TITLE = "System Administration TUI"

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("r", "refresh_dashboard", "Refresh"),
    ]

    def __init__(self, readonly: bool = False):
        super().__init__()
        self.readonly = readonly
        self.root_mode = is_root() and not readonly
        try:
            self.pkg_manager = detect_package_manager()
        except Exception:
            self.pkg_manager = "unknown"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="top-row"):
                yield Static(self.render_monitor(), id="monitor-panel", classes="panel")
                yield Static(self.render_host_info(), id="host-panel", classes="panel")
            with Horizontal(id="bottom-row"):
                items = [ListItem(Label(label)) for _, label, _ in CATEGORIES]
                yield ListView(*items, id="menu-panel", classes="panel")
                yield Static(self.render_welcome(), id="detail-panel", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.refresh_panels)
        self.query_one(ListView).index = 0

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index or 0
        key, label, description = CATEGORIES[idx]
        self.query_one("#detail-panel", Static).update(self.render_category(key, label, description))

    def action_refresh_dashboard(self) -> None:
        self.refresh_panels()

    def refresh_panels(self) -> None:
        self.query_one("#monitor-panel", Static).update(self.render_monitor())
        self.query_one("#host-panel", Static).update(self.render_host_info())

    def _bar(self, percent: float, width: int = 18) -> str:
        filled = int((percent / 100) * width)
        empty = max(0, width - filled)
        color = "green"
        if percent >= 80:
            color = "red"
        elif percent >= 60:
            color = "yellow"
        return f"[{color}]" + ("█" * filled) + f"[/][grey37]" + ("─" * empty) + "[/]"

    def _fmt_uptime(self, seconds: float) -> str:
        seconds = int(seconds)
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        if days:
            return f"{days}j {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def render_monitor(self) -> str:
        cpu = cpu_percent()
        ram = ram_percent()
        disk = disk_percent("/")
        load1, load5, load15 = load_average()
        net = network_counters()
        temp = cpu_temperature()
        temp_str = f"{temp:.1f}°C" if temp is not None else "N/A"
        return (
            "[b]Monitor[/b]\n"
            f"CPU   : {self._bar(cpu)} {cpu:5.1f}%\n"
            f"RAM   : {self._bar(ram)} {ram:5.1f}%\n"
            f"DISK  : {self._bar(disk)} {disk:5.1f}%\n"
            f"LOAD  : {load1:.2f} / {load5:.2f} / {load15:.2f}\n"
            f"NET   : RX {net.bytes_recv // (1024*1024)} MB / TX {net.bytes_sent // (1024*1024)} MB\n"
            f"TEMP  : {temp_str}\n"
            f"UPTIME: {self._fmt_uptime(uptime_seconds())}"
        )

    def render_host_info(self) -> str:
        ips = ", ".join(get_local_ips()) or "N/A"
        sudo_mode = "COMPLET" if self.root_mode else "LIMITE"
        return (
            "[b]Host info[/b]\n"
            f"Hostname : {get_hostname()}\n"
            f"OS       : {get_os_name()}\n"
            f"Kernel   : {get_kernel()}\n"
            f"IP       : {ips}\n"
            f"Pkg mgr  : {self.pkg_manager}\n"
            f"Mode     : {sudo_mode}\n"
            f"Version  : {__version__}"
        )

    def render_welcome(self) -> str:
        mode = "Mode sudo complet" if self.root_mode else "Mode limité sans sudo. Certaines actions sont désactivées."
        return (
            "[b]Systek V2[/b]\n\n"
            "Sélectionne une catégorie à gauche.\n\n"
            f"{mode}\n"
            "Relance avec : sudo systek"
        )

    def render_category(self, key: str, label: str, description: str) -> str:
        blocks = {
            "system": (
                "1. Mettre à jour le système\n"
                "2. Redémarrer le serveur\n"
                "3. Éteindre le serveur"
            ),
            "packages": (
                "4. Installer un paquet\n"
                "5. Supprimer un paquet\n"
                "6. Exclure un paquet des mises à jour\n"
                "7. Réinclure un paquet\n"
                "8. Rechercher un paquet"
            ),
            "services": (
                "9. Redémarrer un service\n"
                "10. Démarrer un service\n"
                "11. Arrêter un service\n"
                "12. Activer un service\n"
                "13. Désactiver un service\n"
                "14. Lister les services\n"
                "15. Surveiller un service\n"
                "16. Logs d’un service"
            ),
            "monitor": (
                "17. Vue globale des ressources\n"
                "18. Vérifier l’espace disque\n"
                "19. Vérifier les connexions réseau\n"
                "20. Vérifier IP / hostname\n"
                "21. Vérifier l’usage RAM\n"
                "22. Vérifier l’usage CPU\n"
                "23. Vérifier la température CPU"
            ),
            "disks": "24. Monter un disque\n25. Lister les disques connectés",
            "network": "26. Afficher les interfaces réseau\n27. Tester la connectivité",
            "firewall": (
                "28. Afficher le statut UFW\n"
                "29. Activer le firewall\n"
                "30. Désactiver le firewall\n"
                "31. Ajouter une règle\n"
                "32. Supprimer une règle"
            ),
            "tools": "33. Installer Cockpit\n34. Diagnostic système",
            "logs": "35. Voir les logs système\n36. Exporter les logs\n37. Voir les logs d’un service",
            "systek": "38. Mettre à jour Systek\n39. Désinstaller Systek\n40. Afficher la version\n41. Quitter",
        }
        access = "sudo requis pour certaines actions" if not self.root_mode else "toutes les actions admin sont disponibles"
        return f"[b]{label}[/b]\n\n{description}\n\n{blocks.get(key, '')}\n\n[i]{access}[/i]"

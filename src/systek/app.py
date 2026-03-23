from __future__ import annotations

from typing import Dict, List, Tuple

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .core import cockpit, disks, firewall, logs, monitor, network, packages, services, system, updater
from .models import ActionDefinition
from .permissions import is_root
from .version import __version__


ACTIONS: List[ActionDefinition] = [
    ActionDefinition(1, "Système", "Mettre à jour le système", "Met à jour les dépôts et paquets système.", True),
    ActionDefinition(2, "Système", "Redémarrer le serveur", "Redémarre immédiatement la machine.", True),
    ActionDefinition(3, "Système", "Éteindre le serveur", "Éteint immédiatement la machine.", True),
    ActionDefinition(4, "Paquets", "Installer un paquet", "Installe un paquet via le gestionnaire détecté.", True, "<package>"),
    ActionDefinition(5, "Paquets", "Supprimer un paquet", "Supprime un paquet.", True, "<package>"),
    ActionDefinition(6, "Paquets", "Exclure un paquet des mises à jour", "Ajoute un hold sur le paquet.", True, "<package>"),
    ActionDefinition(7, "Paquets", "Réinclure un paquet", "Retire le hold du paquet.", True, "<package>"),
    ActionDefinition(8, "Paquets", "Rechercher un paquet", "Recherche un paquet dans les dépôts.", False, "<package>"),
    ActionDefinition(9, "Services", "Redémarrer un service", "Redémarre un service systemd.", True, "<service>"),
    ActionDefinition(10, "Services", "Démarrer un service", "Démarre un service systemd.", True, "<service>"),
    ActionDefinition(11, "Services", "Arrêter un service", "Arrête un service systemd.", True, "<service>"),
    ActionDefinition(12, "Services", "Activer un service", "Active un service au démarrage.", True, "<service>"),
    ActionDefinition(13, "Services", "Désactiver un service", "Désactive un service au démarrage.", True, "<service>"),
    ActionDefinition(14, "Services", "Lister les services", "Affiche les services systemd.", False),
    ActionDefinition(15, "Services", "Surveiller un service", "Affiche le status systemctl d'un service.", False, "<service>"),
    ActionDefinition(16, "Services", "Logs d’un service", "Affiche les derniers logs journalctl du service.", False, "<service>"),
    ActionDefinition(17, "Surveillance", "Vue globale des ressources", "Affiche CPU, RAM, Disk, load, uptime, température.", False),
    ActionDefinition(18, "Surveillance", "Vérifier l’espace disque", "Affiche l'occupation des points de montage.", False),
    ActionDefinition(19, "Surveillance", "Vérifier les connexions réseau", "Affiche les connexions TCP/UDP.", False),
    ActionDefinition(20, "Surveillance", "Vérifier IP / hostname", "Affiche le hostname et les IP locales.", False),
    ActionDefinition(21, "Surveillance", "Vérifier l’usage RAM", "Affiche l'utilisation mémoire.", False),
    ActionDefinition(22, "Surveillance", "Vérifier l’usage CPU", "Affiche l'utilisation CPU.", False),
    ActionDefinition(23, "Surveillance", "Vérifier la température CPU", "Affiche la température CPU si disponible.", False),
    ActionDefinition(24, "Disques", "Monter un disque", "Monte un périphérique sur un point de montage.", True, "<device> <mountpoint>"),
    ActionDefinition(25, "Disques", "Lister les disques connectés", "Affiche les périphériques bloc.", False),
    ActionDefinition(26, "Réseau", "Afficher les interfaces réseau", "Affiche les interfaces détectées.", False),
    ActionDefinition(27, "Réseau", "Tester la connectivité", "Ping 1.1.1.1 pour un test simple.", False),
    ActionDefinition(28, "Pare-feu", "Afficher le statut UFW", "Affiche les règles UFW.", False),
    ActionDefinition(29, "Pare-feu", "Activer le firewall", "Active UFW. Attention à la session SSH.", True),
    ActionDefinition(30, "Pare-feu", "Désactiver le firewall", "Désactive UFW.", True),
    ActionDefinition(31, "Pare-feu", "Ajouter une règle", "Ajoute une règle UFW allow.", True, "<règle>"),
    ActionDefinition(32, "Pare-feu", "Supprimer une règle", "Supprime une règle UFW par numéro.", True, "<numéro>"),
    ActionDefinition(33, "Outils", "Installer Cockpit", "Installe Cockpit et affiche les URLs possibles.", True),
    ActionDefinition(34, "Outils", "Diagnostic système", "Affiche les informations générales et le mode d'exécution.", False),
    ActionDefinition(35, "Systek", "Mettre à jour Systek", "Met à jour l'installation locale de Systek.", True),
    ActionDefinition(36, "Systek", "Désinstaller Systek", "Indique la commande de désinstallation.", True),
    ActionDefinition(37, "Systek", "Afficher la version", "Affiche la version de l'application.", False),
    ActionDefinition(38, "Systek", "Quitter", "Ferme l'application.", False),
]


class MetricBox(Static):
    value = reactive("--")
    subtitle = reactive("")

    def __init__(self, title: str, metric_id: str) -> None:
        super().__init__(id=metric_id, classes="metric-box")
        self.title = title

    def watch_value(self, value: str) -> None:
        self.update(Text.from_markup(f"[b]{self.title}[/b]\n{value}\n{self.subtitle}"))

    def watch_subtitle(self, subtitle: str) -> None:
        self.update(Text.from_markup(f"[b]{self.title}[/b]\n{self.value}\n{subtitle}"))


class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quitter"),
        Binding("r", "refresh_dashboard", "Rafraîchir"),
        Binding("/", "focus_command", "Commande"),
        Binding("enter", "run_selected", "Exécuter"),
        Binding("tab", "cycle_focus", "Changer focus"),
    ]

    selected_category = reactive("Système")

    def __init__(self) -> None:
        super().__init__()
        self.root_mode = is_root()
        self.pkg_manager = packages.detect_package_manager()
        self.categories = list(dict.fromkeys(a.category for a in ACTIONS))
        self.category_actions: Dict[str, List[ActionDefinition]] = {
            category: [a for a in ACTIONS if a.category == category] for category in self.categories
        }
        self.action_lookup = {a.number: a for a in ACTIONS}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="app-root"):
            with Horizontal(id="metrics-row"):
                yield MetricBox("CPU", "m-cpu")
                yield MetricBox("RAM", "m-ram")
                yield MetricBox("DISK /", "m-disk")
                yield MetricBox("NET", "m-net")
                yield MetricBox("LOAD", "m-load")
                yield MetricBox("UPTIME", "m-uptime")
            with Horizontal(id="main-row"):
                with Container(id="sidebar"):
                    yield Label("Catégories", classes="section-title")
                    yield ListView(*[ListItem(Label(cat)) for cat in self.categories], id="category-list")
                with Container(id="center-pane"):
                    yield Label("Actions", classes="section-title")
                    yield ListView(id="action-list")
                with Container(id="right-pane"):
                    yield Static(id="host-panel", classes="box-panel")
                    yield Static(id="detail-panel", classes="box-panel")
                    yield Static(id="result-panel", classes="box-panel")
            with Horizontal(id="command-row"):
                yield Input(placeholder="Commande rapide: ex 9 nginx | 4 htop | 31 22/tcp", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Systek"
        self.sub_title = "Linux Admin TUI"
        self.refresh_dashboard()
        category_list = self.query_one("#category-list", ListView)
        category_list.index = 0
        self.load_actions_for_category(self.categories[0])
        self.update_host_panel()
        self.update_detail_panel(self.category_actions[self.categories[0]][0])
        self.query_one("#result-panel", Static).update("[b]Résultat[/b]\nPrêt.")

    def action_cycle_focus(self) -> None:
        current = self.focused
        widgets = [
            self.query_one("#category-list", ListView),
            self.query_one("#action-list", ListView),
            self.query_one("#command-input", Input),
        ]
        if current not in widgets:
            widgets[0].focus()
            return
        idx = widgets.index(current)
        widgets[(idx + 1) % len(widgets)].focus()

    def action_focus_command(self) -> None:
        self.query_one("#command-input", Input).focus()

    def action_refresh_dashboard(self) -> None:
        self.refresh_dashboard()
        self.update_host_panel()

    def action_run_selected(self) -> None:
        if isinstance(self.focused, Input):
            self.execute_command_bar(self.focused.value)
            return
        action_list = self.query_one("#action-list", ListView)
        action = self.get_selected_action(action_list)
        if action:
            self.run_selected_action(action, [])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "category-list":
            cat = self.extract_label(event.item)
            self.selected_category = cat
            self.load_actions_for_category(cat)
            first_action = self.category_actions[cat][0]
            self.update_detail_panel(first_action)
        elif event.list_view.id == "action-list":
            action = self.get_selected_action(event.list_view)
            if action:
                self.update_detail_panel(action)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "command-input":
            self.execute_command_bar(event.value)
            event.input.value = ""

    def on_key(self, event: events.Key) -> None:
        if self.focused and self.focused.id in {"category-list", "action-list"}:
            if event.key in {"up", "down"}:
                # let ListView handle movement, then refresh detail after a tiny delay via call_after_refresh
                self.call_after_refresh(self._sync_detail_from_focus)

    def _sync_detail_from_focus(self) -> None:
        if self.focused and self.focused.id == "action-list":
            action = self.get_selected_action(self.focused)
            if action:
                self.update_detail_panel(action)

    def extract_label(self, item: ListItem) -> str:
        label = item.query_one(Label)
        return str(label.renderable)

    def get_selected_action(self, action_list: ListView) -> ActionDefinition | None:
        if action_list.index is None:
            return None
        actions = self.category_actions[self.selected_category]
        if 0 <= action_list.index < len(actions):
            return actions[action_list.index]
        return None

    def load_actions_for_category(self, category: str) -> None:
        action_list = self.query_one("#action-list", ListView)
        action_list.clear()
        for action in self.category_actions[category]:
            suffix = " [sudo]" if action.requires_root else ""
            label = f"{action.number:>2}. {action.label}{suffix}"
            action_list.append(ListItem(Label(label)))
        action_list.index = 0
        action_list.focus()

    def refresh_dashboard(self) -> None:
        cpu = monitor.cpu_percent()
        ram = monitor.ram_percent()
        disk_pct = monitor.disk_percent("/")
        rx, tx = monitor.net_summary()
        la = monitor.load_average()
        temp = monitor.cpu_temperature()

        self.query_one("#m-cpu", MetricBox).value = self.progress_bar(cpu, "%")
        self.query_one("#m-cpu", MetricBox).subtitle = f"Temp: {temp:.1f}°C" if temp is not None else "Temp: N/A"
        self.query_one("#m-ram", MetricBox).value = self.progress_bar(ram, "%")
        self.query_one("#m-ram", MetricBox).subtitle = "Mémoire"
        self.query_one("#m-disk", MetricBox).value = self.progress_bar(disk_pct, "%")
        self.query_one("#m-disk", MetricBox).subtitle = "Occupation"
        self.query_one("#m-net", MetricBox).value = f"RX {rx}\nTX {tx}"
        self.query_one("#m-net", MetricBox).subtitle = "Trafic total"
        self.query_one("#m-load", MetricBox).value = f"{la[0]:.2f} {la[1]:.2f} {la[2]:.2f}"
        self.query_one("#m-load", MetricBox).subtitle = "1 / 5 / 15 min"
        self.query_one("#m-uptime", MetricBox).value = monitor.uptime_human()
        self.query_one("#m-uptime", MetricBox).subtitle = "Depuis boot"

    def progress_bar(self, value: float, suffix: str) -> str:
        filled = max(0, min(20, int(round(value / 5))))
        empty = 20 - filled
        style = "green" if value < 60 else "yellow" if value < 85 else "red"
        return f"[{style}]{'█' * filled}[/]{'░' * empty}\n{value:>5.1f}{suffix}"

    def update_host_panel(self) -> None:
        ips = ", ".join(network.ip_addresses()) or "N/A"
        mode = "COMPLET" if self.root_mode else "LIMITÉ"
        text = (
            f"[b]Hôte[/b]\n"
            f"Hostname : {system.get_hostname()}\n"
            f"OS       : {system.get_os_name()}\n"
            f"Kernel   : {system.get_kernel()}\n"
            f"IPs      : {ips}\n"
            f"Pkg mgr  : {self.pkg_manager}\n"
            f"Mode     : {mode}\n"
            f"Version  : {__version__}\n\n"
            f"Sans sudo, certaines actions restent disponibles en consultation seulement."
        )
        self.query_one("#host-panel", Static).update(text)

    def update_detail_panel(self, action: ActionDefinition) -> None:
        req = "Oui" if action.requires_root else "Non"
        hint = action.args_hint or "Aucun argument"
        text = (
            f"[b]Action {action.number} — {action.label}[/b]\n"
            f"Catégorie : {action.category}\n"
            f"Sudo      : {req}\n"
            f"Arguments : {hint}\n\n"
            f"{action.description}\n"
        )
        self.query_one("#detail-panel", Static).update(text)

    def execute_command_bar(self, raw: str) -> None:
        parts = raw.strip().split()
        if not parts:
            return
        try:
            number = int(parts[0])
        except ValueError:
            self.show_result("Commande invalide. Exemple: 9 nginx")
            return
        action = self.action_lookup.get(number)
        if not action:
            self.show_result(f"Action inconnue: {number}")
            return
        self.run_selected_action(action, parts[1:])

    def run_selected_action(self, action: ActionDefinition, args: List[str]) -> None:
        if action.requires_root and not self.root_mode:
            self.show_result("Action limitée sans sudo. Relance avec : sudo systek")
            return
        if action.number == 38:
            self.exit()
            return
        result = self.dispatch_action(action, args)
        self.show_result(result)
        self.refresh_dashboard()
        self.update_host_panel()

    def dispatch_action(self, action: ActionDefinition, args: List[str]) -> str:
        try:
            n = action.number
            if n == 1:
                res1, res2 = system.update_system(self.pkg_manager)
                return self.format_results("Update système", [res1, res2])
            if n == 2:
                return self.format_results("Redémarrage", [system.reboot_system()])
            if n == 3:
                return self.format_results("Arrêt", [system.shutdown_system()])
            if n == 4:
                return self.need_arg_or_run(args, "package", lambda x: packages.install_package(self.pkg_manager, x), "Installation paquet")
            if n == 5:
                return self.need_arg_or_run(args, "package", lambda x: packages.remove_package(self.pkg_manager, x), "Suppression paquet")
            if n == 6:
                return self.need_arg_or_run(args, "package", lambda x: packages.hold_package(self.pkg_manager, x), "Hold paquet")
            if n == 7:
                return self.need_arg_or_run(args, "package", lambda x: packages.unhold_package(self.pkg_manager, x), "Unhold paquet")
            if n == 8:
                return self.need_arg_or_run(args, "package", lambda x: packages.search_package(self.pkg_manager, x), "Recherche paquet")
            if n == 9:
                return self.need_arg_or_run(args, "service", services.restart_service, "Restart service")
            if n == 10:
                return self.need_arg_or_run(args, "service", services.start_service, "Start service")
            if n == 11:
                return self.need_arg_or_run(args, "service", services.stop_service, "Stop service")
            if n == 12:
                return self.need_arg_or_run(args, "service", services.enable_service, "Enable service")
            if n == 13:
                return self.need_arg_or_run(args, "service", services.disable_service, "Disable service")
            if n == 14:
                return self.format_results("Liste services", [services.list_services()])
            if n == 15:
                return self.need_arg_or_run(args, "service", services.service_status, "Status service")
            if n == 16:
                return self.need_arg_or_run(args, "service", services.service_logs, "Logs service")
            if n == 17:
                temp = monitor.cpu_temperature()
                return (
                    "Vue ressources\n\n"
                    f"CPU  : {monitor.cpu_percent():.1f}%\n"
                    f"RAM  : {monitor.ram_percent():.1f}%\n"
                    f"DISK : {monitor.disk_percent('/'): .1f}%\n"
                    f"LOAD : {' / '.join(f'{x:.2f}' for x in monitor.load_average())}\n"
                    f"UP   : {monitor.uptime_human()}\n"
                    f"TEMP : {f'{temp:.1f}°C' if temp is not None else 'N/A'}"
                )
            if n == 18:
                return f"Espace disque\n\n{disks.disk_usage_lines()}"
            if n == 19:
                return self.format_results("Connexions réseau", [network.network_connections()])
            if n == 20:
                return f"IP / Hostname\n\nHostname: {network.hostname()}\nIPs: {', '.join(network.ip_addresses()) or 'N/A'}"
            if n == 21:
                return f"RAM\n\nUtilisation mémoire: {monitor.ram_percent():.1f}%"
            if n == 22:
                return f"CPU\n\nUtilisation CPU: {monitor.cpu_percent():.1f}%"
            if n == 23:
                temp = monitor.cpu_temperature()
                return f"Température CPU\n\n{f'{temp:.1f}°C' if temp is not None else 'Non disponible'}"
            if n == 24:
                if len(args) < 2:
                    return "Usage: 24 <device> <mountpoint>"
                return self.format_results("Montage disque", [disks.mount_disk(args[0], args[1])])
            if n == 25:
                return self.format_results("Disques", [disks.list_disks()])
            if n == 26:
                return f"Interfaces réseau\n\n{network.list_interfaces()}"
            if n == 27:
                return self.format_results("Test connectivité", [network.connectivity_test()])
            if n == 28:
                return self.format_results("UFW status", [firewall.ufw_status()])
            if n == 29:
                return self.format_results("UFW enable", [firewall.enable_ufw()])
            if n == 30:
                return self.format_results("UFW disable", [firewall.disable_ufw()])
            if n == 31:
                return self.need_arg_or_run(args, "règle", firewall.add_rule, "Ajout règle UFW")
            if n == 32:
                return self.need_arg_or_run(args, "numéro", firewall.delete_rule, "Suppression règle UFW")
            if n == 33:
                install_result, ips = cockpit.install_cockpit(self.pkg_manager)
                extra = "\n".join(f"https://{ip}:9090" for ip in ips) if ips else "URL non détectée"
                return self.format_results("Installation Cockpit", [install_result]) + f"\n\nAccès possible:\n{extra}"
            if n == 34:
                return (
                    "Diagnostic\n\n"
                    f"OS        : {system.get_os_name()}\n"
                    f"Kernel    : {system.get_kernel()}\n"
                    f"Hostname  : {system.get_hostname()}\n"
                    f"IPs       : {', '.join(network.ip_addresses()) or 'N/A'}\n"
                    f"Pkg mgr   : {self.pkg_manager}\n"
                    f"Mode root : {'oui' if self.root_mode else 'non'}"
                )
            if n == 35:
                return self.format_results("Update Systek", [updater.update_systek()])
            if n == 36:
                return "Désinstallation\n\nCommande: sudo /opt/systek/uninstall.sh"
            if n == 37:
                return f"Version Systek\n\n{__version__}"
            return "Action non implémentée."
        except PermissionError as exc:
            return str(exc)
        except Exception as exc:
            return f"Erreur: {exc}"

    def need_arg_or_run(self, args: List[str], arg_name: str, fn, title: str) -> str:
        if not args:
            return f"Usage: {title} nécessite {arg_name}"
        res = fn(" ".join(args))
        return self.format_results(title, [res])

    def format_results(self, title: str, results) -> str:
        chunks = [f"[b]{title}[/b]"]
        for idx, result in enumerate(results, start=1):
            status = "OK" if result.ok else f"ERREUR ({result.returncode})"
            output = result.stdout or result.stderr or "Aucune sortie"
            trimmed = "\n".join(output.splitlines()[:80])
            chunks.append(f"\n[{idx}] {status}\n{trimmed}")
        return "\n".join(chunks)

    def show_result(self, text: str) -> None:
        self.query_one("#result-panel", Static).update(text)

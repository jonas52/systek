from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .models import ActionSpec
from .permissions import is_root
from .core.packages import (
    detect_package_manager,
    hold_package,
    install_package,
    remove_package,
    search_package,
    unhold_package,
)
from .core.services import (
    disable_service,
    enable_service,
    list_services,
    restart_service,
    service_logs,
    service_status,
    start_service,
    stop_service,
)
from .core.monitor import cpu_percent, cpu_temperature, disk_percent, load_average, network_counters, ram_percent, uptime_seconds
from .core.system import get_hostname, get_kernel, get_os_name, reboot_system, shutdown_system, update_system
from .core.network import connectivity_test, get_local_ips, list_interfaces, network_connections
from .core.disks import disk_usage_report, list_disks, mount_disk
from .core.firewall import add_rule, delete_rule, disable_ufw, enable_ufw, ufw_status
from .core.logs import export_system_logs, system_logs
from .core.cockpit import install_cockpit
from .version import __version__

ACTIONS: list[ActionSpec] = [
    ActionSpec(1, "Mettre à jour le système", "Système", "Met à jour les paquets système.", True),
    ActionSpec(2, "Redémarrer le serveur", "Système", "Redémarrage immédiat.", True),
    ActionSpec(3, "Éteindre le serveur", "Système", "Arrêt immédiat.", True),
    ActionSpec(4, "Installer un paquet", "Paquets", "Installe un paquet via le gestionnaire détecté.", True, "nom_du_paquet"),
    ActionSpec(5, "Supprimer un paquet", "Paquets", "Supprime un paquet.", True, "nom_du_paquet"),
    ActionSpec(6, "Exclure un paquet des mises à jour", "Paquets", "apt-mark hold.", True, "nom_du_paquet"),
    ActionSpec(7, "Réinclure un paquet", "Paquets", "apt-mark unhold.", True, "nom_du_paquet"),
    ActionSpec(8, "Rechercher un paquet", "Paquets", "Recherche un paquet.", False, "mot_cle"),
    ActionSpec(9, "Redémarrer un service", "Services", "Redémarre un service systemd.", True, "nom_du_service"),
    ActionSpec(10, "Démarrer un service", "Services", "Démarre un service systemd.", True, "nom_du_service"),
    ActionSpec(11, "Arrêter un service", "Services", "Arrête un service systemd.", True, "nom_du_service"),
    ActionSpec(12, "Activer un service", "Services", "Active un service au boot.", True, "nom_du_service"),
    ActionSpec(13, "Désactiver un service", "Services", "Désactive un service au boot.", True, "nom_du_service"),
    ActionSpec(14, "Lister les services", "Services", "Liste tous les services."),
    ActionSpec(15, "Surveiller un service", "Services", "Affiche le statut d’un service.", False, "nom_du_service"),
    ActionSpec(16, "Logs d’un service", "Services", "Affiche les derniers logs d’un service.", False, "nom_du_service"),
    ActionSpec(17, "Vue globale des ressources", "Surveillance", "Résumé CPU/RAM/DISK/TEMP."),
    ActionSpec(18, "Vérifier l’espace disque", "Surveillance", "Occupation des partitions."),
    ActionSpec(19, "Vérifier les connexions réseau", "Surveillance", "Sockets réseau via ss."),
    ActionSpec(20, "Vérifier IP / hostname", "Surveillance", "Affiche le hostname et les IP locales."),
    ActionSpec(21, "Vérifier l’usage RAM", "Surveillance", "Affiche l’usage mémoire."),
    ActionSpec(22, "Vérifier l’usage CPU", "Surveillance", "Affiche la charge CPU."),
    ActionSpec(23, "Vérifier la température CPU", "Surveillance", "Affiche la température CPU si disponible."),
    ActionSpec(24, "Monter un disque", "Disques", "Monte un périphérique sur un point de montage.", True, "device point_de_montage"),
    ActionSpec(25, "Lister les disques connectés", "Disques", "Affiche lsblk."),
    ActionSpec(26, "Afficher les interfaces réseau", "Réseau", "Liste les interfaces détectées."),
    ActionSpec(27, "Tester la connectivité", "Réseau", "Ping 1.1.1.1."),
    ActionSpec(28, "Afficher le statut UFW", "Pare-feu", "Affiche le statut UFW."),
    ActionSpec(29, "Activer le firewall", "Pare-feu", "Active UFW.", True),
    ActionSpec(30, "Désactiver le firewall", "Pare-feu", "Désactive UFW.", True),
    ActionSpec(31, "Ajouter une règle", "Pare-feu", "Ajoute une règle UFW.", True, "regle ex: 22/tcp"),
    ActionSpec(32, "Supprimer une règle", "Pare-feu", "Supprime une règle UFW par numéro.", True, "numero_de_regle"),
    ActionSpec(33, "Installer Cockpit", "Outils", "Installe Cockpit.", True),
    ActionSpec(34, "Diagnostic système", "Outils", "Affiche un résumé de diagnostic."),
    ActionSpec(35, "Voir les logs système", "Logs", "Affiche les derniers logs système."),
    ActionSpec(36, "Exporter les logs", "Logs", "Exporte les logs dans /tmp/systek_logs.txt."),
    ActionSpec(37, "Voir les logs d’un service", "Logs", "Alias de l’action 16.", False, "nom_du_service"),
    ActionSpec(38, "Mettre à jour Systek", "Systek", "Affiche la commande d’update.", True),
    ActionSpec(39, "Désinstaller Systek", "Systek", "Affiche la commande de désinstallation.", True),
    ActionSpec(40, "Afficher la version", "Systek", "Affiche la version installée."),
]

ACTION_MAP = {action.number: action for action in ACTIONS}


class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    TITLE = "Systek"
    SUB_TITLE = "Administration Linux"
    BINDINGS = [("q", "quit", "Quitter"), ("r", "refresh_dashboard", "Refresh"), ("enter", "run_selected", "Exécuter")]

    def __init__(self, readonly: bool = False):
        super().__init__()
        self.readonly = readonly
        self.root_mode = is_root() and not readonly
        self.pkg_manager = detect_package_manager()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-layout"):
            with Horizontal(id="top-row"):
                yield Static(id="monitor-panel", classes="panel")
                yield Static(id="host-panel", classes="panel")
            with Horizontal(id="center-row"):
                with Vertical(id="actions-column", classes="panel"):
                    yield Label("Actions", classes="panel-title")
                    items = [ListItem(Label(f"{action.number:>2}. [{action.category}] {action.label}")) for action in ACTIONS]
                    yield ListView(*items, id="action-list")
                with Vertical(id="detail-column", classes="panel"):
                    yield Label("Détail", classes="panel-title")
                    yield Static(id="detail-panel")
                with Vertical(id="output-column", classes="panel"):
                    yield Label("Résultat", classes="panel-title")
                    yield Static(id="output-panel")
            with Container(id="command-row", classes="panel"):
                yield Input(placeholder="Exécuter: 20  | Avec argument: 9 nginx  | 31 22/tcp", id="command-input")
                yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.refresh_dashboard)
        self.query_one("#action-list", ListView).index = 0
        self.refresh_dashboard()
        self.show_action_details(ACTIONS[0].number)
        self.set_status("Prêt. Tape un numéro puis Entrée, ou sélectionne une action et appuie sur Entrée.")

    def action_refresh_dashboard(self) -> None:
        self.refresh_dashboard()
        self.set_status("Dashboard rafraîchi.")

    def refresh_dashboard(self) -> None:
        self.query_one("#monitor-panel", Static).update(self.render_monitor())
        self.query_one("#host-panel", Static).update(self.render_host_info())

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        index = event.list_view.index or 0
        number = ACTIONS[index].number
        self.show_action_details(number)

    def action_run_selected(self) -> None:
        list_view = self.query_one("#action-list", ListView)
        index = list_view.index or 0
        action = ACTIONS[index]
        command_input = self.query_one("#command-input", Input)
        value = command_input.value.strip()
        if value and value.split()[0].isdigit():
            self.execute_command_string(value)
        else:
            payload = str(action.number)
            if value:
                payload += f" {value}"
            self.execute_command_string(payload)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.execute_command_string(event.value)
        event.input.value = ""

    def show_action_details(self, number: int) -> None:
        action = ACTION_MAP[number]
        root = "oui" if action.requires_root else "non"
        hint = action.arg_hint or "aucun"
        text = (
            f"[b]{action.number}. {action.label}[/b]\n\n"
            f"Catégorie : {action.category}\n"
            f"sudo requis : {root}\n"
            f"argument : {hint}\n\n"
            f"{action.description}\n"
        )
        if action.arg_hint:
            text += f"\nExemple : [cyan]{action.number} {action.arg_hint}[/cyan]"
        self.query_one("#detail-panel", Static).update(text)

    def set_status(self, text: str) -> None:
        self.query_one("#status-bar", Static).update(text)

    def render_monitor(self) -> str:
        cpu = cpu_percent()
        ram = ram_percent()
        disk = disk_percent("/")
        load1, load5, load15 = load_average()
        net = network_counters()
        temp = cpu_temperature()
        uptime = self._fmt_uptime(uptime_seconds())
        temp_text = f"{temp:.1f}°C" if temp is not None else "N/A"
        return (
            "[b]Monitor[/b]\n"
            f"CPU   {self._bar(cpu)} {cpu:5.1f}%\n"
            f"RAM   {self._bar(ram)} {ram:5.1f}%\n"
            f"DISK  {self._bar(disk)} {disk:5.1f}%\n"
            f"LOAD  {load1:.2f} / {load5:.2f} / {load15:.2f}\n"
            f"NET   RX {net.bytes_recv // (1024*1024)} MB  TX {net.bytes_sent // (1024*1024)} MB\n"
            f"TEMP  {temp_text}\n"
            f"UP    {uptime}"
        )

    def render_host_info(self) -> str:
        ips = ", ".join(get_local_ips()) or "N/A"
        mode = "COMPLET" if self.root_mode else "LIMITE"
        mode_style = "green" if self.root_mode else "yellow"
        return (
            "[b]Host[/b]\n"
            f"Hostname  {get_hostname()}\n"
            f"OS        {get_os_name()}\n"
            f"Kernel    {get_kernel()}\n"
            f"IP        {ips}\n"
            f"Pkg mgr   {self.pkg_manager}\n"
            f"Mode      [{mode_style}]{mode}[/]\n"
            f"Version   {__version__}"
        )

    def _fmt_uptime(self, seconds: float) -> str:
        s = int(seconds)
        days, s = divmod(s, 86400)
        hours, s = divmod(s, 3600)
        minutes, _ = divmod(s, 60)
        if days:
            return f"{days}j {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _bar(self, percent: float, width: int = 16) -> str:
        filled = max(0, min(width, int((percent / 100) * width)))
        empty = width - filled
        color = "green"
        if percent >= 80:
            color = "red"
        elif percent >= 60:
            color = "yellow"
        return f"[{color}]" + ("█" * filled) + f"[/][grey35]" + ("─" * empty) + "[/]"

    def execute_command_string(self, text: str) -> None:
        raw = text.strip()
        if not raw:
            self.set_status("Aucune action saisie.")
            return
        parts = raw.split()
        if not parts[0].isdigit():
            self.set_status("Commence par un numéro d’action, par exemple 20 ou 9 nginx.")
            return
        number = int(parts[0])
        if number not in ACTION_MAP:
            self.set_status(f"Action inconnue: {number}")
            return
        args = parts[1:]
        self.show_action_details(number)
        action = ACTION_MAP[number]
        if action.requires_root and not self.root_mode:
            self.query_one("#output-panel", Static).update(
                "[yellow]Action limitée.[/] Lance Systek avec [b]sudo systek[/b] pour cette opération."
            )
            self.set_status(f"Action {number} bloquée: sudo requis.")
            return
        result = self.execute_action(number, args)
        self.query_one("#output-panel", Static).update(result)
        self.set_status(f"Action {number} exécutée.")

    def execute_action(self, number: int, args: list[str]) -> str:
        try:
            match number:
                case 1:
                    r1, r2 = update_system(self.pkg_manager)
                    return self._format_results("Update système", [r1, r2])
                case 2:
                    return self._format_results("Redémarrage", [reboot_system()])
                case 3:
                    return self._format_results("Arrêt", [shutdown_system()])
                case 4:
                    self._need_args(args, 1, "Exemple: 4 htop")
                    return self._format_results("Installation paquet", [install_package(self.pkg_manager, args[0])])
                case 5:
                    self._need_args(args, 1, "Exemple: 5 htop")
                    return self._format_results("Suppression paquet", [remove_package(self.pkg_manager, args[0])])
                case 6:
                    self._need_args(args, 1, "Exemple: 6 docker-ce")
                    return self._format_results("Hold paquet", [hold_package(self.pkg_manager, args[0])])
                case 7:
                    self._need_args(args, 1, "Exemple: 7 docker-ce")
                    return self._format_results("Unhold paquet", [unhold_package(self.pkg_manager, args[0])])
                case 8:
                    self._need_args(args, 1, "Exemple: 8 nginx")
                    return self._format_results("Recherche paquet", [search_package(self.pkg_manager, args[0])])
                case 9:
                    self._need_args(args, 1, "Exemple: 9 nginx")
                    return self._format_results("Restart service", [restart_service(args[0])])
                case 10:
                    self._need_args(args, 1, "Exemple: 10 nginx")
                    return self._format_results("Start service", [start_service(args[0])])
                case 11:
                    self._need_args(args, 1, "Exemple: 11 nginx")
                    return self._format_results("Stop service", [stop_service(args[0])])
                case 12:
                    self._need_args(args, 1, "Exemple: 12 nginx")
                    return self._format_results("Enable service", [enable_service(args[0])])
                case 13:
                    self._need_args(args, 1, "Exemple: 13 nginx")
                    return self._format_results("Disable service", [disable_service(args[0])])
                case 14:
                    return self._format_results("Liste services", [list_services()])
                case 15:
                    self._need_args(args, 1, "Exemple: 15 nginx")
                    return self._format_results("Statut service", [service_status(args[0])])
                case 16 | 37:
                    self._need_args(args, 1, "Exemple: 16 nginx")
                    return self._format_results("Logs service", [service_logs(args[0])])
                case 17:
                    return (
                        "[b]Vue globale[/b]\n\n"
                        f"CPU  : {cpu_percent():.1f}%\n"
                        f"RAM  : {ram_percent():.1f}%\n"
                        f"DISK : {disk_percent('/'): .1f}%\n"
                        f"TEMP : {cpu_temperature() if cpu_temperature() is not None else 'N/A'}\n"
                        f"IP   : {', '.join(get_local_ips()) or 'N/A'}"
                    )
                case 18:
                    return f"[b]Espace disque[/b]\n\n{disk_usage_report()}"
                case 19:
                    return self._format_results("Connexions réseau", [network_connections()])
                case 20:
                    return (
                        "[b]IP / hostname[/b]\n\n"
                        f"Hostname : {get_hostname()}\n"
                        f"IP       : {', '.join(get_local_ips()) or 'N/A'}"
                    )
                case 21:
                    return f"[b]RAM[/b]\n\nUtilisation mémoire: {ram_percent():.1f}%"
                case 22:
                    return f"[b]CPU[/b]\n\nUtilisation CPU: {cpu_percent():.1f}%"
                case 23:
                    temp = cpu_temperature()
                    return f"[b]Température CPU[/b]\n\n{temp:.1f}°C" if temp is not None else "[b]Température CPU[/b]\n\nNon disponible."
                case 24:
                    self._need_args(args, 2, "Exemple: 24 /dev/sdb1 /mnt/data")
                    return self._format_results("Montage disque", [mount_disk(args[0], args[1])])
                case 25:
                    return self._format_results("Disques", [list_disks()])
                case 26:
                    return "[b]Interfaces réseau[/b]\n\n" + "\n".join(list_interfaces())
                case 27:
                    return self._format_results("Test connectivité", [connectivity_test()])
                case 28:
                    return self._format_results("Statut UFW", [ufw_status()])
                case 29:
                    return self._format_results("Activation UFW", [enable_ufw()])
                case 30:
                    return self._format_results("Désactivation UFW", [disable_ufw()])
                case 31:
                    self._need_args(args, 1, "Exemple: 31 22/tcp")
                    return self._format_results("Ajout règle UFW", [add_rule(" ".join(args))])
                case 32:
                    self._need_args(args, 1, "Exemple: 32 1")
                    return self._format_results("Suppression règle UFW", [delete_rule(args[0])])
                case 33:
                    result, ips = install_cockpit(self.pkg_manager)
                    text = self._format_results("Installation Cockpit", [result])
                    if ips:
                        text += "\n\nAccès probable : " + ", ".join([f"https://{ip}:9090" for ip in ips])
                    return text
                case 34:
                    return self._doctor_report()
                case 35:
                    return self._format_results("Logs système", [system_logs()])
                case 36:
                    output = "/tmp/systek_logs.txt"
                    result = export_system_logs(output)
                    text = self._format_results("Export logs", [result])
                    if result.ok:
                        text += f"\n\nFichier créé: {output}"
                    return text
                case 38:
                    return "[b]Update Systek[/b]\n\nCommande: [cyan]sudo systek --update[/cyan]"
                case 39:
                    return "[b]Désinstaller Systek[/b]\n\nCommande: [cyan]sudo /opt/systek/uninstall.sh[/cyan]"
                case 40:
                    return f"[b]Version[/b]\n\nSystek {__version__}"
        except PermissionError as exc:
            return f"[yellow]{exc}[/]"
        except NotImplementedError as exc:
            return f"[yellow]{exc}[/]"
        except Exception as exc:
            return f"[red]Erreur[/]\n\n{exc}"
        return "Action non implémentée."

    def _need_args(self, args: list[str], minimum: int, example: str) -> None:
        if len(args) < minimum:
            raise ValueError(f"Argument manquant. {example}")

    def _format_results(self, title: str, results: list) -> str:
        blocks = [f"[b]{title}[/b]"]
        for idx, result in enumerate(results, start=1):
            state = "[green]OK[/]" if result.ok else "[red]ERREUR[/]"
            body = result.stdout or result.stderr or "Aucune sortie"
            blocks.append(f"\n{state} commande #{idx}\n{body}")
        return "\n".join(blocks)

    def _doctor_report(self) -> str:
        ips = ", ".join(get_local_ips()) or "N/A"
        return (
            "[b]Diagnostic[/b]\n\n"
            f"Hostname : {get_hostname()}\n"
            f"OS       : {get_os_name()}\n"
            f"Kernel   : {get_kernel()}\n"
            f"Pkg mgr  : {self.pkg_manager}\n"
            f"IP       : {ips}\n"
            f"Mode     : {'sudo complet' if self.root_mode else 'limité sans sudo'}\n"
            f"CPU      : {cpu_percent():.1f}%\n"
            f"RAM      : {ram_percent():.1f}%\n"
            f"DISK     : {disk_percent('/'):.1f}%\n"
        )

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, RichLog, Static

from .permissions import is_root
from .version import __version__
from .core.actions import ACTIONS_BY_CODE, CATEGORIES, action_lines_for_category, execute_action, parse_command
from .core.monitor import (
    cpu_percent,
    cpu_temperature,
    disk_percent,
    hostname,
    human_bytes,
    load_average,
    local_ips,
    network_rates,
    ram_percent,
    uptime_human,
)
from .core.system import current_user, detect_package_manager, kernel_version, os_pretty_name


class MetricCard(Static):
    def update_metric(self, title: str, value: str, percent: float | None = None, accent: str = "green") -> None:
        bar = ""
        if percent is not None:
            fill = max(0, min(20, int(percent / 5)))
            empty = 20 - fill
            bar_color = "green" if percent < 60 else "yellow" if percent < 85 else "red"
            bar = f"\n[{bar_color}]{'█' * fill}[/]{'·' * empty}"
        self.update(f"[b]{title}[/b]\n[{accent}]{value}[/]{bar}")


class CategoryItem(ListItem):
    def __init__(self, category: str) -> None:
        super().__init__(Label(category))
        self.category = category


class ActionItem(ListItem):
    def __init__(self, code: int, text: str) -> None:
        super().__init__(Label(text))
        self.code = code


class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    TITLE = "Systek"
    SUB_TITLE = "Linux Admin Console"
    BINDINGS = [
        Binding("q", "quit", "Quitter"),
        Binding("r", "refresh_dashboard", "Rafraîchir"),
        Binding("tab", "focus_next", "Champ suivant", show=False),
        Binding("shift+tab", "focus_previous", "Champ précédent", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_category = CATEGORIES[0]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="app-shell"):
            with Grid(id="monitor-grid"):
                yield MetricCard(id="cpu-card")
                yield MetricCard(id="ram-card")
                yield MetricCard(id="disk-card")
                yield MetricCard(id="net-card")
                yield MetricCard(id="load-card")
                yield MetricCard(id="temp-card")

            with Horizontal(id="top-info"):
                yield Static(id="host-panel")
                yield Static(id="mode-panel")

            with Horizontal(id="workspace"):
                with Vertical(classes="column narrow"):
                    yield Label("Sections", classes="panel-title")
                    yield ListView(*[CategoryItem(cat) for cat in CATEGORIES], id="category-list")
                with Vertical(classes="column medium"):
                    yield Label("Actions", classes="panel-title")
                    yield ListView(id="action-list")
                with Vertical(classes="column wide"):
                    yield Label("Détails", classes="panel-title")
                    yield Static(id="detail-panel")
                    yield Label("Résultat", classes="panel-title")
                    yield RichLog(id="result-log", wrap=True, markup=True, highlight=True)

            with Container(id="command-bar"):
                yield Input(placeholder="Commande rapide : ex 14 | 6 nginx | 25 22/tcp", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_dashboard()
        self.refresh_category_actions(self.current_category)
        category_list = self.query_one("#category-list", ListView)
        category_list.index = 0
        self.query_one("#command-input", Input).focus()
        self.set_interval(2.0, self._refresh_dashboard)

    def action_refresh_dashboard(self) -> None:
        self._refresh_dashboard()
        self.notify("Dashboard rafraîchi")

    def _refresh_dashboard(self) -> None:
        cpu = cpu_percent()
        ram = ram_percent()
        disk = disk_percent("/")
        rx, tx = network_rates(0.08)
        l1, l5, l15 = load_average()
        self.query_one("#cpu-card", MetricCard).update_metric("CPU", f"{cpu:.1f}%", cpu)
        self.query_one("#ram-card", MetricCard).update_metric("RAM", f"{ram:.1f}%", ram, "cyan")
        self.query_one("#disk-card", MetricCard).update_metric("DISK /", f"{disk:.1f}%", disk, "magenta")
        self.query_one("#net-card", MetricCard).update_metric("NET", f"RX {human_bytes(rx)}\nTX {human_bytes(tx)}", None, "blue")
        self.query_one("#load-card", MetricCard).update_metric("LOAD", f"{l1:.2f} / {l5:.2f} / {l15:.2f}\nUptime {uptime_human()}", None, "yellow")
        self.query_one("#temp-card", MetricCard).update_metric("TEMP", cpu_temperature(), None, "red")

        ips = ", ".join(local_ips()) or "N/A"
        self.query_one("#host-panel", Static).update(
            "\n".join([
                "[b]Système[/b]",
                f"Host      : {hostname()}",
                f"OS        : {os_pretty_name()}",
                f"Kernel    : {kernel_version()}",
                f"IP        : {ips}",
                f"User      : {current_user()}",
                f"Pkg mgr   : {detect_package_manager()}",
                f"Version   : {__version__}",
            ])
        )
        mode = "ADMIN" if is_root() else "LIMITÉ"
        color = "green" if is_root() else "yellow"
        self.query_one("#mode-panel", Static).update(
            "\n".join([
                "[b]Mode[/b]",
                f"[{color}]{mode}[/]",
                "",
                "Sans sudo : consultation et diagnostic.",
                "Avec sudo : administration complète.",
                "",
                "Commande rapide en bas.",
                "Entrée exécute la commande saisie.",
                "r = refresh, q = quitter",
            ])
        )

    def refresh_category_actions(self, category: str) -> None:
        self.current_category = category
        action_list = self.query_one("#action-list", ListView)
        action_list.clear()
        lines = action_lines_for_category(category)
        for line in lines:
            code = int(line.split(".")[0])
            action_list.append(ActionItem(code, line))
        if lines:
            action_list.index = 0
            first_code = int(lines[0].split(".")[0])
            self.show_action_details(first_code)

    def show_action_details(self, code: int) -> None:
        action = ACTIONS_BY_CODE.get(code)
        if not action:
            return
        root_text = "Oui" if action.requires_root else "Non"
        hint = action.usage or f"{code}"
        example = action.example or hint
        self.query_one("#detail-panel", Static).update(
            "\n".join([
                f"[b]{action.code}. {action.label}[/b]",
                "",
                action.description,
                "",
                f"Section           : {action.category}",
                f"Sudo requis       : {root_text}",
                f"Commande rapide   : {hint}",
                f"Exemple           : {example}",
            ])
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if item is None:
            return
        if event.list_view.id == "category-list" and isinstance(item, CategoryItem):
            self.refresh_category_actions(item.category)
            return
        if event.list_view.id == "action-list" and isinstance(item, ActionItem):
            self.show_action_details(item.code)
            action = ACTIONS_BY_CODE[item.code]
            if action.usage and "<" in action.usage:
                self.query_one("#command-input", Input).value = action.example or action.usage
                self.notify("Complète ou valide la commande en bas")
            else:
                self.execute_from_text(str(item.code))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if event.list_view.id == "action-list" and isinstance(item, ActionItem):
            self.show_action_details(item.code)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return
        raw = event.value.strip()
        if not raw:
            return
        self.execute_from_text(raw)
        event.input.value = ""

    def execute_from_text(self, raw: str) -> None:
        log = self.query_one("#result-log", RichLog)
        code, args = parse_command(raw)
        if code is None:
            self.notify("Commande invalide")
            return
        action = ACTIONS_BY_CODE.get(code)
        if not action:
            self.notify(f"Action inconnue: {code}")
            return
        try:
            result = execute_action(code, args)
        except Exception as exc:
            log.write(f"[bold red]Erreur[/] {exc}")
            log.write("─" * 80)
            return
        status = "OK" if result.ok else "ERROR"
        color = "green" if result.ok else "red"
        log.write(f"[bold {color}]{status}[/] [{action.code}] {action.label}")
        if result.command:
            log.write(f"[dim]$ {result.command}[/]")
        payload = result.stdout or result.stderr or "Aucune sortie"
        for line in payload.splitlines()[:400]:
            log.write(line)
        log.write("─" * 80)


def main() -> None:
    SystekApp().run()

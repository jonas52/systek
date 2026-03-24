from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static
from .core.monitor import human_bytes, human_uptime, snapshot
from .core.system import action_map, execute_action, host_info

class MetricCard(Static):
    DEFAULT_CSS = """
    MetricCard {
        border: round $panel;
        padding: 0 1;
        height: 7;
        background: $surface;
    }
    """

class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    TITLE = "Systek"
    SUB_TITLE = "Admin Linux TUI"
    BINDINGS = [
        Binding("q", "quit", "Quitter"),
        Binding("r", "refresh_data", "Rafraîchir"),
        Binding("enter", "run_selected", "Exécuter"),
        Binding("slash", "focus_command", "Commande"),
    ]

    selected_action = reactive("1")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="screen"):
            with Horizontal(id="monitor-row"):
                yield MetricCard(id="cpu-card")
                yield MetricCard(id="ram-card")
                yield MetricCard(id="disk-card")
                yield MetricCard(id="net-card")
                yield MetricCard(id="load-card")
                yield MetricCard(id="temp-card")
            with Horizontal(id="main-row"):
                with Vertical(id="nav-col"):
                    yield Static("[b]Actions[/b]", classes="panel-title")
                    yield ListView(*[ListItem(Label(f"{k}. {v[0]}"), id=f"item-{k}") for k, v in action_map().items()], id="action-list")
                with Vertical(id="detail-col"):
                    yield Static("[b]Système[/b]", classes="panel-title")
                    yield Static(id="host-panel")
                    yield Static("[b]Détail[/b]", classes="panel-title")
                    yield Static(id="detail-panel")
                    yield Static("[b]Résultat[/b]", classes="panel-title")
                    yield Static(id="result-panel")
            with Container(id="command-row"):
                yield Input(placeholder="Commande rapide : 1, 4, 8 …", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()
        self.update_host_panel()
        self.update_detail_panel()
        self.query_one(ListView).index = 0
        self.query_one("#command-input", Input).blur()

    def action_focus_command(self) -> None:
        self.query_one("#command-input", Input).focus()

    def action_refresh_data(self) -> None:
        data = snapshot()
        self.query_one("#cpu-card", Static).update(self.render_metric("CPU", data["cpu"], "%", "Processeur"))
        self.query_one("#ram-card", Static).update(self.render_metric("RAM", data["ram"], "%", "Mémoire"))
        self.query_one("#disk-card", Static).update(self.render_metric("DISK", data["disk"], "%", "/"))
        self.query_one("#net-card", Static).update(
            f"[b]NET[/b]\nRX {human_bytes(data['rx'])}\nTX {human_bytes(data['tx'])}\n[dim]Trafic cumulé[/dim]"
        )
        l1, l5, l15 = data["load"]
        self.query_one("#load-card", Static).update(
            f"[b]LOAD[/b]\n{l1:.2f} {l5:.2f} {l15:.2f}\nUptime {human_uptime(data['uptime'])}\n[dim]Charge système[/dim]"
        )
        temp = data["temp"]
        self.query_one("#temp-card", Static).update(
            f"[b]TEMP[/b]\n{f'{temp:.1f} °C' if temp is not None else 'N/A'}\n[dim]Capteur CPU[/dim]"
        )

    def render_metric(self, name: str, value: float, suffix: str, subtitle: str) -> str:
        level = "good"
        if value >= 85:
            level = "bad"
        elif value >= 60:
            level = "warn"
        blocks = 20
        filled = max(0, min(blocks, int(round((value / 100) * blocks))))
        bar = "█" * filled + "░" * (blocks - filled)
        color = {"good": "green", "warn": "yellow", "bad": "red"}[level]
        return f"[b]{name}[/b]\n[{color}]{bar}[/{color}]\n[{color}]{value:.1f}{suffix}[/{color}]\n[dim]{subtitle}[/dim]"

    def update_host_panel(self) -> None:
        info = host_info()
        text = (
            f"Hostname : [b]{info['hostname']}[/b]\n"
            f"OS       : {info['os']}\n"
            f"Kernel   : {info['kernel']}\n"
            f"IP       : {info['ips']}\n"
            f"Mode     : {info['sudo']}"
        )
        self.query_one("#host-panel", Static).update(text)

    def update_detail_panel(self) -> None:
        label, need_root, cmd = action_map()[self.selected_action]
        need = "sudo requis" if need_root else "lecture / exécution simple"
        self.query_one("#detail-panel", Static).update(
            f"[b]{self.selected_action}. {label}[/b]\n"
            f"Privilège : {need}\n"
            f"Commande   : {' '.join(cmd)}"
        )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and event.item.id and event.item.id.startswith("item-"):
            self.selected_action = event.item.id.split("-", 1)[1]
            self.update_detail_panel()

    def action_run_selected(self) -> None:
        if self.focused and isinstance(self.focused, Input):
            return
        self.run_selected_action(self.selected_action)

    def run_selected_action(self, key: str) -> None:
        self.query_one("#result-panel", Static).update(execute_action(key))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        key = event.value.strip()
        if key in action_map():
            self.selected_action = key
            lv = self.query_one(ListView)
            lv.index = list(action_map().keys()).index(key)
            self.update_detail_panel()
            self.run_selected_action(key)
        else:
            self.query_one("#result-panel", Static).update("Commande inconnue. Utilise 1 à 8.")
        event.input.value = ""
        event.input.blur()

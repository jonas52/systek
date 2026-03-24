from __future__ import annotations

from collections import OrderedDict

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .core.monitor import human_bytes, human_uptime, snapshot
from .core.system import action_by_key, actions, execute_action, host_info


CSS = """
Screen {
    background: #0b1117;
    color: #d9e2ec;
}

Header {
    background: #111a23;
    color: #dce7f3;
}

Footer {
    background: #111a23;
    color: #dce7f3;
}

#screen {
    layout: vertical;
}

#monitor-row {
    height: 9;
    margin: 0 1;
}

MetricCard {
    border: round #2c4153;
    background: #111922;
    padding: 0 1;
    height: 8;
    width: 1fr;
    margin-right: 1;
}

MetricCard.-last {
    margin-right: 0;
}

#main-row {
    height: 1fr;
    margin: 0 1 1 1;
}

#left-col, #right-col {
    background: #101720;
    border: round #2c4153;
    padding: 1;
}

#left-col {
    width: 40;
    margin-right: 1;
}

#right-col {
    width: 1fr;
}

.section-title {
    color: #8fb7d9;
    text-style: bold;
    margin-bottom: 1;
}

#category-panel, #detail-panel, #result-panel, #host-panel {
    border: round #223240;
    background: #0d141b;
    padding: 1 2;
    margin-bottom: 1;
}

#category-panel {
    height: 7;
}

#action-list {
    border: tall #223240;
    background: #0d141b;
    height: 1fr;
}

#action-list > .list-view--highlight {
    background: #163148;
    color: #f2f7fb;
}

#host-panel {
    height: 7;
}

#detail-panel {
    height: 8;
}

#result-panel {
    height: 1fr;
    overflow-y: auto;
}

#command-input {
    margin: 0 1 1 1;
    border: round #2c4153;
    background: #101720;
}
"""


class MetricCard(Static):
    pass


class SystekApp(App):
    CSS = CSS
    TITLE = "Systek"
    SUB_TITLE = "Admin Linux TUI"
    BINDINGS = [
        Binding("q", "quit", "Quitter"),
        Binding("r", "refresh_dashboard", "Rafraîchir"),
        Binding("enter", "run_selected", "Exécuter"),
        Binding("slash", "focus_command", "Commande"),
    ]

    selected_key = reactive("1")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="screen"):
            with Horizontal(id="monitor-row"):
                yield MetricCard(id="cpu-card")
                yield MetricCard(id="ram-card")
                yield MetricCard(id="disk-card")
                yield MetricCard(id="net-card")
                yield MetricCard(id="load-card")
                yield MetricCard(id="temp-card", classes="-last")
            with Horizontal(id="main-row"):
                with Vertical(id="left-col"):
                    yield Static("Vue d'ensemble", classes="section-title")
                    yield Static(id="category-panel")
                    yield Static("Actions", classes="section-title")
                    items = [ListItem(Label(f"{item['key']}. {item['label']}"), id=f"action-{item['key']}") for item in actions()]
                    yield ListView(*items, id="action-list")
                with Vertical(id="right-col"):
                    yield Static("Système", classes="section-title")
                    yield Static(id="host-panel")
                    yield Static("Détail", classes="section-title")
                    yield Static(id="detail-panel")
                    yield Static("Résultat", classes="section-title")
                    yield Static(id="result-panel")
            yield Input(placeholder="Commande rapide : 1 à 8", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_dashboard()
        self.update_sidebar()
        self.update_host_panel()
        self.update_detail_panel()
        action_list = self.query_one("#action-list", ListView)
        action_list.index = 0
        self.query_one("#command-input", Input).blur()

    def action_focus_command(self) -> None:
        self.query_one("#command-input", Input).focus()

    def action_refresh_dashboard(self) -> None:
        self.refresh_dashboard()
        self.update_host_panel()

    def refresh_dashboard(self) -> None:
        data = snapshot()
        self.query_one("#cpu-card", Static).update(self.render_metric("CPU", float(data["cpu"]), "%", "Processeur"))
        self.query_one("#ram-card", Static).update(self.render_metric("RAM", float(data["ram"]), "%", "Mémoire"))
        self.query_one("#disk-card", Static).update(self.render_metric("DISK", float(data["disk"]), "%", "/"))
        self.query_one("#net-card", Static).update(
            f"[b]NET[/b]\nRX {human_bytes(float(data['rx']))}\nTX {human_bytes(float(data['tx']))}\n[dim]Trafic cumulé[/dim]"
        )
        l1, l5, l15 = data["load"]
        self.query_one("#load-card", Static).update(
            f"[b]LOAD[/b]\n{l1:.2f} {l5:.2f} {l15:.2f}\nUptime {human_uptime(int(data['uptime']))}\n[dim]Charge système[/dim]"
        )
        temp = data["temp"]
        temp_text = f"{temp:.1f} °C" if isinstance(temp, (int, float)) else "N/A"
        self.query_one("#temp-card", Static).update(f"[b]TEMP[/b]\n{temp_text}\n[dim]Capteur CPU[/dim]")

    def render_metric(self, name: str, value: float, suffix: str, subtitle: str) -> str:
        level = "green"
        if value >= 85:
            level = "red"
        elif value >= 60:
            level = "yellow"
        blocks = 18
        filled = max(0, min(blocks, int(round((value / 100) * blocks))))
        bar = "█" * filled + "░" * (blocks - filled)
        return f"[b]{name}[/b]\n[{level}]{bar}[/{level}]\n[{level}]{value:.1f}{suffix}[/{level}]\n[dim]{subtitle}[/dim]"

    def update_sidebar(self) -> None:
        grouped: OrderedDict[str, list[str]] = OrderedDict()
        for item in actions():
            grouped.setdefault(str(item["category"]), []).append(f"{item['key']}. {item['label']}")
        lines: list[str] = []
        for category, entries in grouped.items():
            lines.append(f"[b]{category}[/b]")
            lines.extend(f"  {entry}" for entry in entries)
            lines.append("")
        lines.append("[dim]Sans sudo : mode limité[/dim]")
        lines.append("[dim]Avec sudo : administration complète[/dim]")
        self.query_one("#category-panel", Static).update("\n".join(lines).strip())

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
        action = action_by_key(self.selected_key)
        if action is None:
            self.query_one("#detail-panel", Static).update("Aucune action sélectionnée.")
            return
        privilege = "sudo requis" if bool(action["root"]) else "lecture / exécution simple"
        command = " ".join(str(x) for x in action["cmd"])
        text = (
            f"[b]{action['key']}. {action['label']}[/b]\n"
            f"Catégorie : {action['category']}\n"
            f"Privilège : {privilege}\n"
            f"Commande  : {command}\n\n"
            f"[dim]{action['description']}[/dim]"
        )
        self.query_one("#detail-panel", Static).update(text)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and event.item.id and event.item.id.startswith("action-"):
            self.selected_key = event.item.id.split("-", 1)[1]
            self.update_detail_panel()

    def action_run_selected(self) -> None:
        if isinstance(self.focused, Input):
            return
        self.run_selected_action(self.selected_key)

    def run_selected_action(self, key: str) -> None:
        self.query_one("#result-panel", Static).update(execute_action(key))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        key = event.value.strip()
        action = action_by_key(key)
        if action is None:
            self.query_one("#result-panel", Static).update("Commande inconnue. Utilise une action de 1 à 8.")
        else:
            self.selected_key = key
            action_keys = [str(item["key"]) for item in actions()]
            self.query_one("#action-list", ListView).index = action_keys.index(key)
            self.update_detail_panel()
            self.run_selected_action(key)
        event.input.value = ""
        event.input.blur()

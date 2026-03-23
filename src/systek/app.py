from __future__ import annotations

from collections import defaultdict

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from .actions import ACTIONS
from .models import Action
from .ops import dashboard_snapshot, execute_action, host_snapshot
from .permissions import is_root


class MetricPanel(Static):
    data = reactive({}, recompose=False)

    def render(self) -> Text:
        snap = dashboard_snapshot()
        t = Text()
        t.append(" Monitor\n", style="bold #7dd3fc")
        t.append(" CPU   ", style="bold")
        t.append(bar(snap["cpu"]), style=color_from_percent(snap["cpu"]))
        t.append(f" {snap['cpu']}\n", style="bold")
        t.append(" RAM   ", style="bold")
        t.append(bar(snap["ram"]), style=color_from_percent(snap["ram"]))
        t.append(f" {snap['ram']}\n", style="bold")
        t.append(" DISK  ", style="bold")
        t.append(bar(snap["disk"]), style=color_from_percent(snap["disk"]))
        t.append(f" {snap['disk']}\n", style="bold")
        t.append(f" LOAD  {snap['load']}\n", style="#e5e7eb")
        t.append(f" NET   {snap['net']}\n", style="#e5e7eb")
        t.append(f" UP    {snap['uptime']}", style="#e5e7eb")
        return t


class HostPanel(Static):
    def render(self) -> Text:
        snap = host_snapshot()
        t = Text()
        t.append(" Host\n", style="bold #86efac")
        for key in ("hostname", "user", "os", "kernel", "ip", "pkg", "mode", "version"):
            label = key.upper().ljust(9)
            value = snap[key]
            style = "#fca5a5" if key == "mode" and snap[key] != "admin" else "#e5e7eb"
            t.append(label, style="bold")
            t.append(f" {value}\n", style=style)
        return t


class ActionList(ListView):
    def __init__(self, actions: list[Action]) -> None:
        self.actions = actions
        items: list[ListItem] = []
        grouped: dict[str, list[Action]] = defaultdict(list)
        for action in actions:
            grouped[action.category].append(action)
        for category, entries in grouped.items():
            items.append(ListItem(Label(f"[{category}]", classes="category-label"), classes="category-item", disabled=True))
            for index, action in enumerate(entries, start=1):
                label = Label(action.label)
                label.tooltip = action.description
                item = ListItem(label)
                item.action_ref = action  # type: ignore[attr-defined]
                items.append(item)
        super().__init__(*items, id="action-list")


class DetailPanel(Static):
    def show_action(self, action: Action) -> None:
        text = (
            f"[b]{action.label}[/b]\n\n"
            f"Catégorie : {action.category}\n"
            f"Privilège requis : {'sudo/root' if action.requires_root else 'lecture seule'}\n\n"
            f"{action.description}\n"
        )
        if action.prompt:
            text += f"\nArgument attendu : {action.prompt}"
        if action.example:
            text += f"\nExemple : {action.example}"
        self.update(text)


class OutputPanel(Static):
    def show_message(self, title: str, body: str, ok: bool = True) -> None:
        status = "OK" if ok else "ERREUR"
        color = "#86efac" if ok else "#fca5a5"
        self.update(f"[b {color}]{status}[/b {color}] [b]{title}[/b]\n\n{body}")


class SystekApp(App):
    CSS_PATH = "../../assets/systek.tcss"
    TITLE = "Systek"
    SUB_TITLE = "Linux admin console"
    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("r", "refresh_ui", "Rafraîchir"),
        ("enter", "launch_selected", "Exécuter"),
        ("slash", "focus_command", "Commande"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.selectable_actions = [a for a in ACTIONS]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="root"):
            with Horizontal(id="top"):
                yield MetricPanel(id="metrics")
                yield HostPanel(id="host")
            with Horizontal(id="middle"):
                yield ActionList(self.selectable_actions)
                with Vertical(id="right-stack"):
                    yield DetailPanel("Sélectionne une action à gauche.", id="details")
                    yield OutputPanel("Résultats en attente.", id="output")
            with Horizontal(id="command-bar"):
                mode = "admin" if is_root() else "limité"
                note = "mode complet" if is_root() else "mode lecture/consultation, relance avec sudo systek"
                yield Static(f"[b]Mode[/b] : {mode}  •  {note}", id="statusline")
                yield Input(placeholder="Entrez l'argument requis puis Entrée. Exemple: nginx ou 22/tcp", id="command")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2, self._refresh_panels)
        self._refresh_panels()
        self.call_after_refresh(self._focus_list)

    def _focus_list(self) -> None:
        self.query_one(ActionList).focus()
        self._sync_current_selection()

    def _refresh_panels(self) -> None:
        self.query_one(MetricPanel).refresh()
        self.query_one(HostPanel).refresh()

    def action_refresh_ui(self) -> None:
        self._refresh_panels()
        self._sync_current_selection()

    def action_focus_command(self) -> None:
        self.query_one("#command", Input).focus()

    def action_launch_selected(self) -> None:
        self._execute_current()

    @on(ListView.Highlighted)
    def on_list_highlighted(self, event: ListView.Highlighted) -> None:
        self._sync_current_selection()

    @on(Input.Submitted, "#command")
    def on_command_submitted(self, event: Input.Submitted) -> None:
        self._execute_current()
        event.input.value = ""
        self.query_one(ActionList).focus()

    def _current_action(self) -> Action | None:
        lv = self.query_one(ActionList)
        item = lv.highlighted_child
        if item is None:
            return None
        return getattr(item, "action_ref", None)

    def _sync_current_selection(self) -> None:
        action = self._current_action()
        details = self.query_one(DetailPanel)
        if action is None:
            details.update("Sélectionne une action disponible.")
            return
        details.show_action(action)

    def _execute_current(self) -> None:
        action = self._current_action()
        if action is None:
            self.query_one(OutputPanel).show_message("Aucune action", "Aucune action exécutable n'est sélectionnée.", False)
            return
        raw_args = self.query_one("#command", Input).value
        result = execute_action(action.key, raw_args)
        self.query_one(OutputPanel).show_message(result.title, result.body, result.ok)


def percent_from_text(value: str) -> int:
    try:
        return int(float(value.replace("%", "").strip()))
    except Exception:
        return 0


def color_from_percent(value: str) -> str:
    pct = percent_from_text(value)
    if pct < 60:
        return "#86efac"
    if pct < 85:
        return "#fde68a"
    return "#fca5a5"


def bar(value: str, width: int = 18) -> str:
    pct = max(0, min(100, percent_from_text(value)))
    filled = int((pct / 100) * width)
    return "█" * filled + "░" * (width - filled)

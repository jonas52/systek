from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..permissions import is_root
from ..shell import CommandResult, run_command
from .system import detect_package_manager


@dataclass(slots=True)
class ActionDef:
    code: int
    category: str
    label: str
    description: str
    requires_root: bool = False
    usage: str = ""
    example: str = ""


CATEGORIES = [
    "Système",
    "Paquets",
    "Services",
    "Surveillance",
    "Disques",
    "Réseau",
    "Pare-feu",
    "Logs",
    "Outils",
]


ACTIONS: list[ActionDef] = [
    ActionDef(1, "Système", "Mettre à jour le système", "Lance la mise à jour du système avec le gestionnaire détecté.", True),
    ActionDef(2, "Paquets", "Installer un paquet", "Installe un paquet système.", True, "2 <paquet>", "2 htop"),
    ActionDef(3, "Paquets", "Supprimer un paquet", "Supprime un paquet système.", True, "3 <paquet>", "3 nginx"),
    ActionDef(4, "Système", "Redémarrer le serveur", "Redémarre la machine après confirmation.", True),
    ActionDef(5, "Système", "Éteindre le serveur", "Éteint la machine après confirmation.", True),
    ActionDef(6, "Services", "Redémarrer un service", "Redémarre un service systemd.", True, "6 <service>", "6 nginx"),
    ActionDef(7, "Services", "Activer un service", "Active un service au démarrage.", True, "7 <service>", "7 ssh"),
    ActionDef(8, "Services", "Désactiver un service", "Désactive un service au démarrage.", True, "8 <service>", "8 apache2"),
    ActionDef(9, "Services", "Lister les services", "Affiche la liste des services systemd."),
    ActionDef(10, "Services", "Surveiller un service", "Affiche le statut détaillé d’un service.", False, "10 <service>", "10 cron.service"),
    ActionDef(11, "Surveillance", "Vue ressources système", "Affiche top en mode interactif."),
    ActionDef(12, "Surveillance", "Espace disque", "Affiche l’occupation disque."),
    ActionDef(13, "Réseau", "Connexions réseau", "Affiche les sockets réseau."),
    ActionDef(14, "Réseau", "IP et hostname", "Affiche les IP locales et le nom d’hôte."),
    ActionDef(15, "Surveillance", "Usage RAM", "Affiche l’utilisation mémoire."),
    ActionDef(16, "Surveillance", "Usage CPU", "Affiche les informations CPU."),
    ActionDef(17, "Surveillance", "Température CPU", "Affiche la température CPU si disponible."),
    ActionDef(18, "Disques", "Monter un disque", "Monte un périphérique sur un point de montage.", True, "18 <device> <mountpoint>", "18 /dev/sdb1 /mnt/data"),
    ActionDef(19, "Disques", "Lister les disques", "Affiche les périphériques bloc."),
    ActionDef(20, "Logs", "Voir les logs système", "Affiche les derniers logs système."),
    ActionDef(21, "Logs", "Sauvegarder les logs", "Exporte des logs système dans un fichier.", False, "21 <fichier>", "21 /tmp/systek-logs.txt"),
    ActionDef(22, "Pare-feu", "Statut UFW", "Affiche le statut du firewall UFW."),
    ActionDef(23, "Pare-feu", "Activer UFW", "Active le firewall UFW.", True),
    ActionDef(24, "Pare-feu", "Désactiver UFW", "Désactive le firewall UFW.", True),
    ActionDef(25, "Pare-feu", "Ajouter une règle UFW", "Ajoute une règle UFW.", True, "25 <règle>", "25 22/tcp"),
    ActionDef(26, "Pare-feu", "Supprimer une règle UFW", "Supprime une règle UFW par numéro ou valeur.", True, "26 <numéro|règle>", "26 1"),
    ActionDef(27, "Outils", "Installer Cockpit", "Installe Cockpit avec le gestionnaire de paquets.", True),
    ActionDef(28, "Paquets", "Exclure un paquet des updates", "Met un paquet en hold (APT uniquement).", True, "28 <paquet>", "28 nginx"),
    ActionDef(29, "Paquets", "Réinclure un paquet", "Retire le hold d’un paquet (APT uniquement).", True, "29 <paquet>", "29 nginx"),
]

ACTIONS_BY_CODE = {a.code: a for a in ACTIONS}


def action_lines_for_category(category: str) -> list[str]:
    return [f"{a.code:>2}. {a.label}" for a in ACTIONS if a.category == category]


def parse_command(raw: str) -> tuple[int | None, list[str]]:
    chunks = raw.strip().split()
    if not chunks:
        return None, []
    try:
        return int(chunks[0]), chunks[1:]
    except ValueError:
        return None, chunks[1:]


def _need_root(action: ActionDef) -> CommandResult | None:
    if action.requires_root and not is_root():
        return CommandResult(False, "", "Cette action nécessite sudo/root.", 1, str(action.code))
    return None


def _pkg_install_cmd(package: str) -> list[str]:
    pm = detect_package_manager()
    return {
        "apt": ["apt", "install", "-y", package],
        "dnf": ["dnf", "install", "-y", package],
        "yum": ["yum", "install", "-y", package],
        "pacman": ["pacman", "-S", "--noconfirm", package],
        "zypper": ["zypper", "install", "-y", package],
        "apk": ["apk", "add", package],
    }.get(pm, ["sh", "-lc", "echo Gestionnaire non supporté && false"])


def _pkg_remove_cmd(package: str) -> list[str]:
    pm = detect_package_manager()
    return {
        "apt": ["apt", "remove", "-y", package],
        "dnf": ["dnf", "remove", "-y", package],
        "yum": ["yum", "remove", "-y", package],
        "pacman": ["pacman", "-R", "--noconfirm", package],
        "zypper": ["zypper", "remove", "-y", package],
        "apk": ["apk", "del", package],
    }.get(pm, ["sh", "-lc", "echo Gestionnaire non supporté && false"])


def _pkg_update_cmds() -> list[list[str]]:
    pm = detect_package_manager()
    return {
        "apt": [["apt", "update"], ["apt", "upgrade", "-y"]],
        "dnf": [["dnf", "upgrade", "--refresh", "-y"]],
        "yum": [["yum", "update", "-y"]],
        "pacman": [["pacman", "-Syu", "--noconfirm"]],
        "zypper": [["zypper", "refresh"], ["zypper", "update", "-y"]],
        "apk": [["apk", "update"], ["apk", "upgrade"]],
    }.get(pm, [["sh", "-lc", "echo Gestionnaire non supporté && false"]])


def execute_action(code: int, args: list[str]) -> CommandResult:
    action = ACTIONS_BY_CODE.get(code)
    if not action:
        return CommandResult(False, "", f"Action inconnue: {code}", 2, str(code))
    root_error = _need_root(action)
    if root_error:
        return root_error

    if code == 1:
        outputs: list[str] = []
        for cmd in _pkg_update_cmds():
            result = run_command(cmd, timeout=3600)
            outputs.append(f"$ {' '.join(cmd)}\n{result.stdout or result.stderr}")
            if not result.ok:
                return CommandResult(False, "\n\n".join(outputs), result.stderr, result.returncode, "update_system")
        return CommandResult(True, "\n\n".join(outputs), "", 0, "update_system")
    if code == 2:
        if not args:
            return CommandResult(False, "", "Usage: 2 <paquet>", 2, "2")
        return run_command(_pkg_install_cmd(args[0]), timeout=3600)
    if code == 3:
        if not args:
            return CommandResult(False, "", "Usage: 3 <paquet>", 2, "3")
        return run_command(_pkg_remove_cmd(args[0]), timeout=3600)
    if code == 4:
        return run_command(["reboot"])
    if code == 5:
        return run_command(["poweroff"])
    if code == 6:
        return run_command(["systemctl", "restart", _arg1(args, "service")])
    if code == 7:
        return run_command(["systemctl", "enable", _arg1(args, "service")])
    if code == 8:
        return run_command(["systemctl", "disable", _arg1(args, "service")])
    if code == 9:
        return run_command(["systemctl", "list-units", "--type=service", "--no-pager"], timeout=120)
    if code == 10:
        return run_command(["systemctl", "status", _arg1(args, "service"), "--no-pager"], timeout=120)
    if code == 11:
        return run_command(["top", "-b", "-n", "1"], timeout=30)
    if code == 12:
        return run_command(["df", "-h"], timeout=30)
    if code == 13:
        if _has_cmd("ss"):
            return run_command(["ss", "-tunap"], timeout=60)
        return run_command(["netstat", "-tulpen"], timeout=60)
    if code == 14:
        if _has_cmd("hostname"):
            host = run_command(["hostname"])
            ip = run_command(["hostname", "-I"])
            return CommandResult(True, f"Hostname: {host.stdout}\nIP: {ip.stdout}", "", 0, "hostname -I")
    if code == 15:
        return run_command(["free", "-h"], timeout=30)
    if code == 16:
        return run_command(["sh", "-lc", "lscpu || cat /proc/cpuinfo | head -40"], timeout=30)
    if code == 17:
        return run_command(["sh", "-lc", "sensors 2>/dev/null || echo 'Température indisponible. Installe lm-sensors.'"], timeout=30)
    if code == 18:
        if len(args) < 2:
            return CommandResult(False, "", "Usage: 18 <device> <mountpoint>", 2, "18")
        prep = run_command(["mkdir", "-p", args[1]])
        if not prep.ok:
            return prep
        return run_command(["mount", args[0], args[1]], timeout=60)
    if code == 19:
        return run_command(["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE"])
    if code == 20:
        if _has_cmd("journalctl"):
            return run_command(["journalctl", "-n", "120", "--no-pager"], timeout=120)
        return run_command(["tail", "-n", "120", "/var/log/syslog"], timeout=30)
    if code == 21:
        if not args:
            return CommandResult(False, "", "Usage: 21 <fichier>", 2, "21")
        res = execute_action(20, [])
        if res.ok:
            with open(args[0], "w", encoding="utf-8") as f:
                f.write(res.stdout)
            return CommandResult(True, f"Logs sauvegardés dans {args[0]}", "", 0, "save_logs")
        return res
    if code == 22:
        return run_command(["ufw", "status", "numbered"], timeout=30)
    if code == 23:
        return run_command(["ufw", "--force", "enable"], timeout=60)
    if code == 24:
        return run_command(["ufw", "disable"], timeout=60)
    if code == 25:
        if not args:
            return CommandResult(False, "", "Usage: 25 <règle>", 2, "25")
        return run_command(["ufw", "allow", args[0]], timeout=60)
    if code == 26:
        if not args:
            return CommandResult(False, "", "Usage: 26 <numéro|règle>", 2, "26")
        return run_command(["ufw", "--force", "delete", args[0]], timeout=60)
    if code == 27:
        return run_command(_pkg_install_cmd("cockpit"), timeout=3600)
    if code == 28:
        if detect_package_manager() != "apt":
            return CommandResult(False, "", "Disponible seulement avec APT.", 2, "28")
        return run_command(["apt-mark", "hold", _arg1(args, "paquet")])
    if code == 29:
        if detect_package_manager() != "apt":
            return CommandResult(False, "", "Disponible seulement avec APT.", 2, "29")
        return run_command(["apt-mark", "unhold", _arg1(args, "paquet")])
    return CommandResult(False, "", "Action non implémentée.", 3, str(code))


def _arg1(args: list[str], name: str) -> str:
    if not args:
        raise ValueError(f"Argument manquant: {name}")
    return args[0]


def _has_cmd(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None

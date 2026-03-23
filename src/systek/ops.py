from __future__ import annotations

import os
import shlex
import socket
import subprocess
import time
from pathlib import Path

import psutil

from .models import ActionResult
from .permissions import is_root
from .systeminfo import hostname, kernel, local_ips, os_pretty_name, package_manager, user_name
from .version import __version__


def _run(cmd: list[str], timeout: int = 25) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _fmt_completed(title: str, proc: subprocess.CompletedProcess[str]) -> ActionResult:
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    code = proc.returncode
    body = []
    body.append(f"$ {' '.join(shlex.quote(x) for x in proc.args)}")
    body.append(f"exit code: {code}")
    if out:
        body.append("\nstdout:\n" + out)
    if err:
        body.append("\nstderr:\n" + err)
    if not out and not err:
        body.append("\nCommande exécutée sans sortie.")
    return ActionResult(title=title, body="\n".join(body), ok=(code == 0))


def _need_root(title: str) -> ActionResult:
    return ActionResult(
        title=title,
        ok=False,
        body=(
            "Cette action nécessite sudo/root.\n"
            "Relance Systek avec : sudo systek\n\n"
            "Sans sudo, le mode reste volontairement limité aux actions de consultation."
        ),
    )


def dashboard_snapshot() -> dict[str, str]:
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    nio = psutil.net_io_counters()
    uptime = int(time.time() - psutil.boot_time())
    hrs, rem = divmod(uptime, 3600)
    mins, secs = divmod(rem, 60)
    return {
        "cpu": f"{cpu:.0f}%",
        "ram": f"{ram:.0f}%",
        "disk": f"{disk:.0f}%",
        "load": f"{load[0]:.2f} {load[1]:.2f} {load[2]:.2f}",
        "net": f"RX {nio.bytes_recv // 1024**2}M / TX {nio.bytes_sent // 1024**2}M",
        "uptime": f"{hrs}h {mins}m {secs}s",
    }


def host_snapshot() -> dict[str, str]:
    ips = ", ".join(local_ips()) or "N/A"
    return {
        "hostname": hostname(),
        "user": user_name(),
        "os": os_pretty_name(),
        "kernel": kernel(),
        "ip": ips,
        "pkg": package_manager(),
        "mode": "admin" if is_root() else "limité",
        "version": __version__,
    }


def execute_action(action_key: str, raw_args: str) -> ActionResult:
    args = raw_args.strip().split()
    pm = package_manager()

    try:
        match action_key:
            case "system.update":
                if not is_root():
                    return _need_root("Mise à jour système")
                if pm == "apt":
                    p1 = _run(["apt", "update"])
                    p2 = _run(["apt", "upgrade", "-y"], timeout=3600)
                    return ActionResult("Mise à jour système", _fmt_completed("apt update", p1).body + "\n\n" + _fmt_completed("apt upgrade", p2).body, p1.returncode == 0 and p2.returncode == 0)
                if pm in {"dnf", "yum"}:
                    proc = _run([pm, "upgrade", "-y"], timeout=3600)
                    return _fmt_completed("Mise à jour système", proc)
                if pm == "pacman":
                    proc = _run(["pacman", "-Syu", "--noconfirm"], timeout=3600)
                    return _fmt_completed("Mise à jour système", proc)
                return ActionResult("Mise à jour système", "Gestionnaire de paquets non supporté.", False)
            case "system.reboot":
                if not is_root():
                    return _need_root("Redémarrage serveur")
                return _fmt_completed("Redémarrage serveur", _run(["reboot"]))
            case "system.shutdown":
                if not is_root():
                    return _need_root("Extinction serveur")
                return _fmt_completed("Extinction serveur", _run(["poweroff"]))
            case "pkg.install":
                if not is_root():
                    return _need_root("Installer un paquet")
                if not args:
                    return ActionResult("Installer un paquet", "Argument attendu : nom du paquet\nExemple : htop", False)
                pkg = args[0]
                cmd = {
                    "apt": ["apt", "install", "-y", pkg],
                    "dnf": ["dnf", "install", "-y", pkg],
                    "yum": ["yum", "install", "-y", pkg],
                    "pacman": ["pacman", "-S", "--noconfirm", pkg],
                }.get(pm)
                if not cmd:
                    return ActionResult("Installer un paquet", "Gestionnaire non supporté.", False)
                return _fmt_completed(f"Installer {pkg}", _run(cmd, timeout=3600))
            case "pkg.remove":
                if not is_root():
                    return _need_root("Supprimer un paquet")
                if not args:
                    return ActionResult("Supprimer un paquet", "Argument attendu : nom du paquet\nExemple : nginx", False)
                pkg = args[0]
                cmd = {
                    "apt": ["apt", "remove", "-y", pkg],
                    "dnf": ["dnf", "remove", "-y", pkg],
                    "yum": ["yum", "remove", "-y", pkg],
                    "pacman": ["pacman", "-R", "--noconfirm", pkg],
                }.get(pm)
                if not cmd:
                    return ActionResult("Supprimer un paquet", "Gestionnaire non supporté.", False)
                return _fmt_completed(f"Supprimer {pkg}", _run(cmd, timeout=3600))
            case "pkg.hold":
                if not is_root():
                    return _need_root("Exclure un paquet")
                if pm != "apt":
                    return ActionResult("Exclure un paquet", "Fonction disponible officiellement sur apt/apt-mark.", False)
                if not args:
                    return ActionResult("Exclure un paquet", "Argument attendu : nom du paquet\nExemple : docker-ce", False)
                return _fmt_completed(f"Hold {args[0]}", _run(["apt-mark", "hold", args[0]]))
            case "pkg.unhold":
                if not is_root():
                    return _need_root("Réinclure un paquet")
                if pm != "apt":
                    return ActionResult("Réinclure un paquet", "Fonction disponible officiellement sur apt/apt-mark.", False)
                if not args:
                    return ActionResult("Réinclure un paquet", "Argument attendu : nom du paquet\nExemple : docker-ce", False)
                return _fmt_completed(f"Unhold {args[0]}", _run(["apt-mark", "unhold", args[0]]))
            case "service.restart":
                if not is_root():
                    return _need_root("Redémarrer un service")
                if not args:
                    return ActionResult("Redémarrer un service", "Argument attendu : nom du service\nExemple : nginx", False)
                return _fmt_completed(f"Restart {args[0]}", _run(["systemctl", "restart", args[0]]))
            case "service.start":
                if not is_root():
                    return _need_root("Démarrer un service")
                if not args:
                    return ActionResult("Démarrer un service", "Argument attendu : nom du service\nExemple : ssh", False)
                return _fmt_completed(f"Start {args[0]}", _run(["systemctl", "start", args[0]]))
            case "service.stop":
                if not is_root():
                    return _need_root("Arrêter un service")
                if not args:
                    return ActionResult("Arrêter un service", "Argument attendu : nom du service\nExemple : nginx", False)
                return _fmt_completed(f"Stop {args[0]}", _run(["systemctl", "stop", args[0]]))
            case "service.enable":
                if not is_root():
                    return _need_root("Activer un service")
                if not args:
                    return ActionResult("Activer un service", "Argument attendu : nom du service\nExemple : ssh", False)
                return _fmt_completed(f"Enable {args[0]}", _run(["systemctl", "enable", args[0]]))
            case "service.disable":
                if not is_root():
                    return _need_root("Désactiver un service")
                if not args:
                    return ActionResult("Désactiver un service", "Argument attendu : nom du service\nExemple : apache2", False)
                return _fmt_completed(f"Disable {args[0]}", _run(["systemctl", "disable", args[0]]))
            case "service.list":
                return _fmt_completed("Liste des services", _run(["systemctl", "list-units", "--type=service", "--no-pager", "--plain"], timeout=60))
            case "service.status":
                if not args:
                    return ActionResult("Statut service", "Argument attendu : nom du service\nExemple : nginx", False)
                return _fmt_completed(f"Statut {args[0]}", _run(["systemctl", "status", args[0], "--no-pager"], timeout=60))
            case "service.logs":
                if not args:
                    return ActionResult("Logs service", "Argument attendu : nom du service\nExemple : nginx", False)
                return _fmt_completed(f"Logs {args[0]}", _run(["journalctl", "-u", args[0], "-n", "120", "--no-pager"], timeout=60))
            case "monitor.overview":
                snap = dashboard_snapshot()
                body = "\n".join([f"CPU   : {snap['cpu']}", f"RAM   : {snap['ram']}", f"Disk  : {snap['disk']}", f"Load  : {snap['load']}", f"Net   : {snap['net']}", f"Uptime: {snap['uptime']}"])
                return ActionResult("Vue globale des ressources", body)
            case "monitor.disk":
                return _fmt_completed("Espace disque", _run(["df", "-h"]))
            case "monitor.net":
                if Path("/usr/bin/ss").exists() or Path("/bin/ss").exists():
                    return _fmt_completed("Connexions réseau", _run(["ss", "-tunap"], timeout=60))
                return _fmt_completed("Connexions réseau", _run(["netstat", "-tulpn"], timeout=60))
            case "monitor.ip":
                ips = "\n".join(local_ips()) or "N/A"
                return ActionResult("IP / Hostname", f"Hostname : {hostname()}\nIP locales:\n{ips}")
            case "monitor.ram":
                vm = psutil.virtual_memory()
                return ActionResult("Usage RAM", f"Total : {vm.total // 1024**2} MiB\nUsed  : {vm.used // 1024**2} MiB\nFree  : {vm.available // 1024**2} MiB\nUsage : {vm.percent:.1f}%")
            case "monitor.cpu":
                per = psutil.cpu_percent(interval=0.3, percpu=True)
                body = [f"CPU global : {psutil.cpu_percent(interval=0.2):.1f}%", ""]
                body.extend([f"Core {idx:02d}: {value:5.1f}%" for idx, value in enumerate(per)])
                return ActionResult("Usage CPU", "\n".join(body))
            case "monitor.temp":
                temps = psutil.sensors_temperatures()
                if not temps:
                    return ActionResult("Température CPU", "Aucune sonde détectée. Installer lm-sensors si nécessaire.", False)
                lines = []
                for chip, entries in temps.items():
                    lines.append(f"[{chip}]")
                    for entry in entries:
                        lines.append(f"- {entry.label or 'sensor'} : {entry.current}°C")
                return ActionResult("Température CPU", "\n".join(lines))
            case "disk.mount":
                if not is_root():
                    return _need_root("Monter un disque")
                if len(args) < 2:
                    return ActionResult("Monter un disque", "Arguments attendus : <device> <mountpoint>\nExemple : /dev/sdb1 /mnt/data", False)
                os.makedirs(args[1], exist_ok=True)
                return _fmt_completed("Monter un disque", _run(["mount", args[0], args[1]]))
            case "disk.list":
                return _fmt_completed("Disques connectés", _run(["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE"], timeout=30))
            case "network.ifaces":
                lines = []
                for name, addrs in psutil.net_if_addrs().items():
                    lines.append(f"[{name}]")
                    for addr in addrs:
                        fam = getattr(addr.family, "name", str(addr.family))
                        lines.append(f"- {fam}: {addr.address}")
                    lines.append("")
                return ActionResult("Interfaces réseau", "\n".join(lines).strip())
            case "network.ping":
                target = args[0] if args else "1.1.1.1"
                return _fmt_completed(f"Connectivité {target}", _run(["ping", "-c", "2", target], timeout=15))
            case "fw.status":
                return _fmt_completed("Statut UFW", _run(["ufw", "status", "numbered"], timeout=30))
            case "fw.enable":
                if not is_root():
                    return _need_root("Activer UFW")
                return _fmt_completed("Activer UFW", _run(["ufw", "--force", "enable"], timeout=60))
            case "fw.disable":
                if not is_root():
                    return _need_root("Désactiver UFW")
                return _fmt_completed("Désactiver UFW", _run(["ufw", "disable"], timeout=60))
            case "fw.allow":
                if not is_root():
                    return _need_root("Ajouter règle UFW")
                if not args:
                    return ActionResult("Ajouter règle UFW", "Argument attendu : règle\nExemple : 22/tcp", False)
                return _fmt_completed(f"Allow {args[0]}", _run(["ufw", "allow", args[0]], timeout=60))
            case "fw.delete":
                if not is_root():
                    return _need_root("Supprimer règle UFW")
                if not args:
                    return ActionResult("Supprimer règle UFW", "Argument attendu : numéro de règle\nExemple : 3", False)
                return _fmt_completed(f"Delete rule {args[0]}", _run(["ufw", "--force", "delete", args[0]], timeout=60))
            case "logs.system":
                return _fmt_completed("Logs système", _run(["journalctl", "-n", "120", "--no-pager"], timeout=60))
            case "tool.cockpit":
                if not is_root():
                    return _need_root("Installer Cockpit")
                cmd = {
                    "apt": ["apt", "install", "-y", "cockpit"],
                    "dnf": ["dnf", "install", "-y", "cockpit"],
                    "yum": ["yum", "install", "-y", "cockpit"],
                    "pacman": ["pacman", "-S", "--noconfirm", "cockpit"],
                }.get(pm)
                if not cmd:
                    return ActionResult("Installer Cockpit", "Gestionnaire non supporté.", False)
                proc = _run(cmd, timeout=3600)
                ip = (local_ips() or ["localhost"])[0]
                msg = _fmt_completed("Installer Cockpit", proc).body
                msg += f"\n\nAccès recommandé : https://{ip}:9090"
                return ActionResult("Installer Cockpit", msg, proc.returncode == 0)
            case "tool.doctor":
                checks = [
                    f"Python : {os.sys.version.split()[0]}",
                    f"Mode root : {'oui' if is_root() else 'non'}",
                    f"OS : {os_pretty_name()}",
                    f"Kernel : {kernel()}",
                    f"Package manager : {pm}",
                    f"IP : {', '.join(local_ips()) or 'N/A'}",
                ]
                return ActionResult("Diagnostic système", "\n".join(checks))
            case "app.update":
                if not is_root():
                    return _need_root("Mettre à jour Systek")
                install_dir = "/opt/systek"
                git_dir = Path(install_dir) / ".git"
                if not git_dir.exists():
                    return ActionResult("Mettre à jour Systek", "Installation non Git dans /opt/systek : update automatique indisponible.", False)
                p1 = _run(["git", "-C", install_dir, "pull", "origin", "main"], timeout=120)
                p2 = _run([f"{install_dir}/.venv/bin/pip", "install", "-r", f"{install_dir}/requirements.txt"], timeout=1200)
                return ActionResult("Mettre à jour Systek", _fmt_completed("git pull", p1).body + "\n\n" + _fmt_completed("pip install", p2).body, p1.returncode == 0 and p2.returncode == 0)
            case "app.uninstall":
                if not is_root():
                    return _need_root("Désinstaller Systek")
                return ActionResult("Désinstaller Systek", "Commande recommandée : sudo /opt/systek/uninstall.sh", True)
            case "app.version":
                return ActionResult("Version Systek", f"Systek {__version__}")
            case _:
                return ActionResult("Action inconnue", f"Action non gérée : {action_key}", False)
    except subprocess.TimeoutExpired as exc:
        return ActionResult("Timeout", f"La commande a dépassé le délai autorisé.\n{exc}", False)
    except FileNotFoundError as exc:
        return ActionResult("Commande introuvable", f"Binaire introuvable : {exc}", False)
    except Exception as exc:  # noqa: BLE001
        return ActionResult("Erreur", f"{type(exc).__name__}: {exc}", False)

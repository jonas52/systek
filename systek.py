#!/usr/bin/env python3
"""Systek - simple Linux admin CLI.

This version keeps the original menu-driven style, translates the UI to English,
and provides a cleaner self-update flow.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable

SERVICE_NAME = "systek"
INSTALL_PATH = Path("/opt/systek")
BIN_PATH = Path(f"/usr/local/bin/{SERVICE_NAME}")
SCRIPT_DIR = Path(__file__).resolve().parent
SUPPORTED_PACKAGE_MANAGERS: dict[str, list[list[str]]] = {
    "apt-get": [["apt-get", "update"], ["apt-get", "upgrade", "-y"]],
    "dnf": [["dnf", "upgrade", "--refresh", "-y"]],
    "yum": [["yum", "update", "-y"]],
    "pacman": [["pacman", "-Syu", "--noconfirm"]],
    "zypper": [["zypper", "refresh"], ["zypper", "update", "-y"]],
    "apk": [["apk", "update"], ["apk", "upgrade"]],
}


def clear_screen() -> None:
    os.system("clear")


def pause() -> None:
    input("╰─╼ Press Enter to continue...")


def run_command(
    command: list[str],
    *,
    check: bool = True,
    capture: bool = False,
    quiet: bool = False,
) -> subprocess.CompletedProcess[str]:
    kwargs: dict[str, object] = {"text": True}
    if capture or quiet:
        kwargs["capture_output"] = True
    result = subprocess.run(command, **kwargs)
    if check and result.returncode != 0:
        stderr = (result.stderr or "").strip() if capture or quiet else ""
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=stderr)
    return result



def require_root() -> None:
    if os.geteuid() != 0:
        print("╰─╼ This script must be run as superuser (root).")
        sys.exit(1)



def detect_package_manager() -> str | None:
    for manager in SUPPORTED_PACKAGE_MANAGERS:
        if shutil.which(manager):
            return manager
    return None



def get_primary_ipv4() -> str | None:
    try:
        result = run_command(["ip", "-4", "route", "get", "1.1.1.1"], capture=True)
        match = re.search(r"src\s+(\d+\.\d+\.\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None



def get_hostname() -> str:
    return socket.gethostname()



def confirm(prompt: str) -> bool:
    answer = input(f"│ {prompt} (y/N) : ").strip().lower()
    return answer in {"y", "yes"}



def update_systek() -> None:
    clear_screen()
    print("│ Updating Systek")

    repo_dir = INSTALL_PATH if (INSTALL_PATH / ".git").is_dir() else SCRIPT_DIR
    if not (repo_dir / ".git").is_dir():
        print("│ No Git repository found.")
        print("│ Self-update is only available for Git-based installations.")
        pause()
        return

    try:
        run_command(["git", "-C", str(repo_dir), "pull", "origin", "main"], quiet=False)

        requirements_file = repo_dir / "requirements.txt"
        if requirements_file.exists():
            pip_path = INSTALL_PATH / ".venv" / "bin" / "pip"
            if pip_path.exists():
                run_command([str(pip_path), "install", "-r", str(requirements_file)], quiet=False)
            elif shutil.which("pip3"):
                run_command(["pip3", "install", "-r", str(requirements_file)], quiet=False)

        print("│ Systek update completed successfully.")
        print("│ Restart the program to use the new version.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Update failed: {exc}")
    pause()



def remove_systek() -> None:
    clear_screen()
    print("│ Removing Systek")
    if not confirm("Are you sure you want to remove Systek?"):
        print("│ Removal cancelled.")
        pause()
        return

    subprocess.run(["systemctl", "stop", SERVICE_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "disable", SERVICE_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["rm", "-f", f"/etc/systemd/system/{SERVICE_NAME}.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "reset-failed"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["rm", "-f", str(BIN_PATH)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["rm", "-rf", str(INSTALL_PATH)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("│ Systek has been removed.")
    pause()



def restart_service() -> None:
    clear_screen()
    print("│ Restart a service")
    service = input("│ Service name to restart : ").strip()
    try:
        run_command(["systemctl", "restart", service])
        print(f"│ Service '{service}' restarted successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to restart service '{service}': {exc}")
    pause()



def restart_server() -> None:
    clear_screen()
    print("│ Reboot the server")
    if not confirm("Are you sure you want to reboot the server?"):
        print("│ Reboot cancelled.")
        pause()
        return
    try:
        run_command(["reboot"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Reboot failed: {exc}")
        pause()



def shutdown_server() -> None:
    clear_screen()
    print("│ Shut down the server")
    if not confirm("Are you sure you want to power off the server?"):
        print("│ Shutdown cancelled.")
        pause()
        return
    try:
        run_command(["poweroff"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Shutdown failed: {exc}")
        pause()



def update_system() -> None:
    clear_screen()
    print("│ System update")
    package_manager = detect_package_manager()
    if not package_manager:
        print("│ No supported package manager found on this system.")
        pause()
        return
    try:
        for command in SUPPORTED_PACKAGE_MANAGERS[package_manager]:
            run_command(command)
        print(f"│ System update completed successfully with {package_manager}.")
    except subprocess.CalledProcessError as exc:
        print(f"│ System update failed with {package_manager}: {exc}")
    pause()



def enable_service() -> None:
    clear_screen()
    print("│ Enable a service")
    service = input("│ Service name to enable : ").strip()
    try:
        run_command(["systemctl", "enable", service])
        print(f"│ Service '{service}' enabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to enable service '{service}': {exc}")
    pause()



def disable_service() -> None:
    clear_screen()
    print("│ Disable a service")
    service = input("│ Service name to disable : ").strip()
    try:
        run_command(["systemctl", "disable", service])
        print(f"│ Service '{service}' disabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to disable service '{service}': {exc}")
    pause()



def list_services() -> None:
    clear_screen()
    print("│ List of services")
    try:
        run_command(["systemctl", "list-units", "--type=service", "--no-pager"])
        print("│ Service list displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to list services: {exc}")
    pause()



def monitor_service() -> None:
    clear_screen()
    print("│ Monitor a service")
    service = input("│ Service name to inspect (example: cron.service) : ").strip()
    try:
        run_command(["systemctl", "status", service, "--no-pager"])
        print(f"│ Service '{service}' status displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to show status for '{service}': {exc}")
    pause()



def check_resource_usage() -> None:
    clear_screen()
    print("│ Resource usage")
    try:
        run_command(["top"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to open top: {exc}")
        pause()



def check_disk_space() -> None:
    clear_screen()
    print("│ Disk space")
    try:
        run_command(["df", "-h"])
        print("│ Disk usage displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display disk usage: {exc}")
    pause()



def check_network_connections() -> None:
    clear_screen()
    print("│ Network connections")
    command = ["ss", "-tunap"] if shutil.which("ss") else ["netstat", "-tunap"]
    try:
        run_command(command)
        print("│ Network connections displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display network connections: {exc}")
    pause()



def check_memory_usage() -> None:
    clear_screen()
    print("│ RAM usage")
    try:
        result = run_command(["free", "-m"], capture=True)
        print(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display RAM usage: {exc}")
    pause()



def check_cpu_usage() -> None:
    clear_screen()
    print("│ CPU usage")
    try:
        result = run_command(["top", "-bn", "1"], capture=True)
        cpu_line = next((line for line in result.stdout.splitlines() if line.startswith("%Cpu(s)") or line.startswith("%Cpu")), None)
        if cpu_line:
            print(f"│ {cpu_line}")
        else:
            print(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display CPU usage: {exc}")
    pause()



def check_cpu_temperature() -> None:
    clear_screen()
    print("│ CPU temperature")
    if not shutil.which("sensors"):
        print("│ The 'sensors' command is not available.")
        print("│ Install lm-sensors first.")
        pause()
        return
    try:
        result = run_command(["sensors"], capture=True)
        print(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display CPU temperature: {exc}")
    pause()



def mount_drive() -> None:
    clear_screen()
    print("│ Mount a drive")
    drive = input("│ Device name : ").strip()
    mount_point = input("│ Mount point : ").strip()
    try:
        run_command(["mount", drive, mount_point])
        print("│ Drive mounted successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to mount drive: {exc}")
    pause()



def list_block_devices() -> None:
    clear_screen()
    print("│ List of block devices")
    try:
        run_command(["lsblk", "-fe7"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to list block devices: {exc}")
    pause()



def _stream_command(command: list[str], output_file: Path | None = None) -> None:
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="")
                if output_file is not None:
                    with output_file.open("a", encoding="utf-8") as handle:
                        handle.write(line)
        except KeyboardInterrupt:
            proc.terminate()
            print("\n│ Log streaming stopped.")



def display_logs() -> None:
    clear_screen()
    print("│ View server logs")
    print("│ Press Ctrl+C to stop log streaming.")
    log_file = "/var/log/syslog" if Path("/var/log/syslog").exists() else "/var/log/messages"
    _stream_command(["tail", "-f", log_file])
    pause()



def save_logs() -> None:
    clear_screen()
    print("│ Back up server logs")
    destination = Path("server_logs.log")
    print(f"│ Writing streamed logs to: {destination.resolve()}")
    print("│ Press Ctrl+C to stop log capture.")
    log_file = "/var/log/syslog" if Path("/var/log/syslog").exists() else "/var/log/messages"
    _stream_command(["tail", "-f", log_file], output_file=destination)
    pause()



def add_package() -> None:
    clear_screen()
    print("│ Install a package")
    package_name = input("│ Package name to install : ").strip()
    if not package_name:
        print("│ No package name provided.")
        pause()
        return
    manager = detect_package_manager()
    if manager not in {"apt-get", "dnf", "yum", "pacman", "zypper", "apk"}:
        print("│ Unsupported package manager for package installation.")
        pause()
        return
    commands = {
        "apt-get": ["apt-get", "install", "-y", package_name],
        "dnf": ["dnf", "install", "-y", package_name],
        "yum": ["yum", "install", "-y", package_name],
        "pacman": ["pacman", "-S", "--noconfirm", package_name],
        "zypper": ["zypper", "install", "-y", package_name],
        "apk": ["apk", "add", package_name],
    }
    try:
        run_command(commands[manager])
        print(f"│ Package '{package_name}' installed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to install package '{package_name}': {exc}")
    pause()



def remove_package() -> None:
    clear_screen()
    print("│ Remove a package")
    package_name = input("│ Package name to remove : ").strip()
    if not package_name:
        print("│ No package name provided.")
        pause()
        return
    manager = detect_package_manager()
    commands = {
        "apt-get": ["apt-get", "remove", "-y", package_name],
        "dnf": ["dnf", "remove", "-y", package_name],
        "yum": ["yum", "remove", "-y", package_name],
        "pacman": ["pacman", "-R", "--noconfirm", package_name],
        "zypper": ["zypper", "remove", "-y", package_name],
        "apk": ["apk", "del", package_name],
    }
    if manager not in commands:
        print("│ Unsupported package manager for package removal.")
        pause()
        return
    try:
        run_command(commands[manager])
        print(f"│ Package '{package_name}' removed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to remove package '{package_name}': {exc}")
    pause()



def check_ip_address() -> None:
    clear_screen()
    print("│ Hostname and IP address")
    hostname = get_hostname()
    ip_address = get_primary_ipv4()
    print(f"│ Hostname : {hostname}")
    if ip_address:
        print(f"│ IP address : {ip_address}")
    else:
        print("│ No primary IPv4 address detected.")
    pause()



def ufw_status() -> None:
    clear_screen()
    print("│ UFW firewall status")
    try:
        run_command(["ufw", "status"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display UFW status: {exc}")
    except FileNotFoundError:
        print("│ The 'ufw' command is not available on this system.")
    pause()



def enable_ufw() -> None:
    clear_screen()
    print("│ Enable UFW firewall")
    if not confirm("Are you sure? This may interrupt your SSH session"):
        print("│ UFW enable cancelled.")
        pause()
        return
    try:
        run_command(["ufw", "enable"])
        print("│ UFW enabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to enable UFW: {exc}")
    pause()



def disable_ufw() -> None:
    clear_screen()
    print("│ Disable UFW firewall")
    if not confirm("Are you sure? This may interrupt your SSH session"):
        print("│ UFW disable cancelled.")
        pause()
        return
    try:
        run_command(["ufw", "disable"])
        print("│ UFW disabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to disable UFW: {exc}")
    pause()



def add_ufw_rules() -> None:
    clear_screen()
    print("│ Add a UFW rule")
    rule = input("│ Port or rule to allow (example: 22/tcp) : ").strip()
    if not rule:
        print("│ No rule provided.")
        pause()
        return
    if not confirm(f"Are you sure you want to allow '{rule}'?"):
        print("│ Rule creation cancelled.")
        pause()
        return
    try:
        run_command(["ufw", "allow", rule])
        print(f"│ Rule '{rule}' added successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to add rule '{rule}': {exc}")
    pause()



def remove_ufw_rules() -> None:
    clear_screen()
    print("│ Remove a UFW rule")
    try:
        run_command(["ufw", "status", "numbered"])
        rule = input("│ Rule number to delete : ").strip()
        if not rule:
            print("│ No rule number provided.")
            pause()
            return
        if not confirm(f"Are you sure you want to delete rule '{rule}'?"):
            print("│ Rule deletion cancelled.")
            pause()
            return
        run_command(["ufw", "delete", rule])
        print(f"│ Rule '{rule}' removed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to remove rule: {exc}")
    pause()



def install_cockpit() -> None:
    clear_screen()
    print("│ Install Cockpit")
    manager = detect_package_manager()
    commands = {
        "apt-get": ["apt-get", "install", "-y", "cockpit"],
        "dnf": ["dnf", "install", "-y", "cockpit"],
        "yum": ["yum", "install", "-y", "cockpit"],
        "pacman": ["pacman", "-S", "--noconfirm", "cockpit"],
        "zypper": ["zypper", "install", "-y", "cockpit"],
    }
    if manager not in commands:
        print("│ Unsupported package manager for Cockpit installation.")
        pause()
        return
    try:
        run_command(commands[manager])
        ip_address = get_primary_ipv4() or "<server-ip>"
        print("│ Cockpit installed successfully.")
        print(f"│ Open: https://{ip_address}:9090")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to install Cockpit: {exc}")
    pause()



def hold_package() -> None:
    clear_screen()
    print("│ Exclude a package from updates")
    package_name = input("│ Package name to hold : ").strip()
    if not package_name:
        print("│ No package name provided.")
        pause()
        return
    if not shutil.which("apt-mark"):
        print("│ Package hold is currently supported on APT-based systems only.")
        pause()
        return
    try:
        run_command(["apt-mark", "hold", package_name])
        print(f"│ Package '{package_name}' excluded successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to hold package '{package_name}': {exc}")
    pause()



def unhold_package() -> None:
    clear_screen()
    print("│ Re-include a package in updates")
    package_name = input("│ Package name to unhold : ").strip()
    if not package_name:
        print("│ No package name provided.")
        pause()
        return
    if not shutil.which("apt-mark"):
        print("│ Package unhold is currently supported on APT-based systems only.")
        pause()
        return
    try:
        run_command(["apt-mark", "unhold", package_name])
        print(f"│ Package '{package_name}' included successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to unhold package '{package_name}': {exc}")
    pause()



def print_menu() -> None:
    clear_screen()
    print(r'''
 ___  _  _  ___  ____  ____  _  _ 
/ __)( \/ )/ __)(_  _)( ___)( )/ )
\__ \ \  / \__ \  )(   )__)  )  ( 
(___/ (__) (___/ (__) (____)(_ )_)
                    By Jonas52
│ 1  Update the system
│ 2  Install a package
│ 3  Remove a package
│ 4  Reboot the server
│ 5  Shut down the server
│ 6  Restart a service
│ 7  Enable a service
│ 8  Disable a service
│ 9  List services
│ 10 Monitor a service
│ 11 Check resource usage
│ 12 Check disk space
│ 13 Check network connections
│ 14 Show hostname and IP address
│ 15 Check RAM usage
│ 16 Check CPU usage
│ 17 Check CPU temperature
│ 18 Mount a drive
│ 19 List connected disks
│ 20 View server logs
│ 21 Save server logs
│ 22 Show UFW status
│ 23 Enable UFW
│ 24 Disable UFW
│ 25 Add a UFW rule
│ 26 Delete a UFW rule
│ 27 Install Cockpit
│ 28 Exclude a package from updates
│ 29 Re-include a package in updates
│ u  Update Systek
│ r  Remove Systek
│ q  Exit
╰──────────────────────────────────────────────────╼
''')


ACTIONS = {
    "1": update_system,
    "2": add_package,
    "3": remove_package,
    "4": restart_server,
    "5": shutdown_server,
    "6": restart_service,
    "7": enable_service,
    "8": disable_service,
    "9": list_services,
    "10": monitor_service,
    "11": check_resource_usage,
    "12": check_disk_space,
    "13": check_network_connections,
    "14": check_ip_address,
    "15": check_memory_usage,
    "16": check_cpu_usage,
    "17": check_cpu_temperature,
    "18": mount_drive,
    "19": list_block_devices,
    "20": display_logs,
    "21": save_logs,
    "22": ufw_status,
    "23": enable_ufw,
    "24": disable_ufw,
    "25": add_ufw_rules,
    "26": remove_ufw_rules,
    "27": install_cockpit,
    "28": hold_package,
    "29": unhold_package,
    "u": update_systek,
    "r": remove_systek,
}



def execute_option(option: str) -> bool:
    normalized = option.strip().lower()
    if normalized in {"q", "e", "exit"}:
        clear_screen()
        return False

    action = ACTIONS.get(normalized)
    if action is None:
        print("╰─╼ Invalid option. Please enter a valid choice.")
        subprocess.run(["sleep", "1"])
        return True

    try:
        action()
    except KeyboardInterrupt:
        print("\n│ Action interrupted by user.")
        pause()
    except Exception as exc:
        print(f"│ An unexpected error occurred: {exc}")
        pause()
    return True



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Systek command options")
    parser.add_argument("--update", action="store_true", help="Update Systek from Git")
    parser.add_argument("--remove", action="store_true", help="Remove Systek completely")
    return parser.parse_args()



def main() -> int:
    if sys.version_info < (3, 10):
        print("╰─╼ This script requires Python 3.10 or later.")
        return 1

    require_root()
    args = parse_args()

    if args.update:
        update_systek()
        return 0
    if args.remove:
        remove_systek()
        return 0

    running = True
    while running:
        print_menu()
        option = input("├──╼ Choose an option : ")
        running = execute_option(option)

    clear_screen()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

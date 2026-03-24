#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "systek"
INSTALL_PATH = "/opt/systek"
BIN_PATH = f"/usr/local/bin/{SERVICE_NAME}"
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
REPO_URL = "https://github.com/jonas52/systek/"
VERBOSE = False

if sys.version_info < (3, 10):
    print("╰─╼ This script requires Python 3.10 or later.")
    sys.exit(1)


def clear_screen():
    os.system("clear")


def press_enter():
    input("╰─╼ Press Enter to continue...")


def title(text: str):
    clear_screen()
    print(f"│ {text}")


def print_status(prefix: str, text: str):
    print(f"│ {prefix} {text}")


def print_error(text: str):
    print(f"│ Error: {text}")


def run_command(command, shell=False, capture=True):
    try:
        if capture and not VERBOSE:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(command, shell=shell, text=True)
            if result.stdout is None:
                result.stdout = ""
            if result.stderr is None:
                result.stderr = ""
        return result.returncode == 0, (result.stdout or ""), (result.stderr or "")
    except FileNotFoundError as exc:
        return False, "", str(exc)
    except Exception as exc:
        return False, "", str(exc)


def require_root():
    if os.geteuid() != 0:
        print("╰─╼ This script must be run as superuser (root).")
        sys.exit(1)


def detect_package_manager():
    for manager in ("apt", "dnf", "yum", "pacman", "zypper", "apk"):
        if shutil.which(manager):
            return manager
    return None


def get_local_ip():
    try:
        ok, out, _ = run_command(["ip", "-4", "addr", "show"], capture=True)
        if ok:
            ips = []
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    ip = line.split()[1].split("/")[0]
                    if not ip.startswith("127."):
                        ips.append(ip)
            if ips:
                return ", ".join(ips)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return "Unavailable"


def command_output(command, empty_message="No data available."):
    ok, out, err = run_command(command, capture=True)
    if ok:
        print(out.strip() or empty_message)
    else:
        print_error(err.strip() or "Command failed.")
    press_enter()


def parse_apt_upgradable_lines(output: str):
    packages = []
    for line in output.splitlines():
        if "/" in line and not line.startswith("Listing..."):
            package = line.split("/", 1)[0].strip()
            if package:
                packages.append(package)
    return packages


def parse_needrestart(output: str):
    restarted = []
    deferred = []
    containers_message = None
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("systemctl restart "):
            service = line.replace("systemctl restart ", "").strip()
            restarted.append(service)
        elif "/etc/needrestart/" in line or "deferred" in line.lower():
            deferred.append(line)
        elif "No containers need to be restarted" in line:
            containers_message = line
    return restarted, deferred, containers_message


def summarize_update_result(package_names, upgrade_stdout, package_manager):
    if package_manager != "apt":
        return

    print_status("•", f"Packages to upgrade: {len(package_names)}")
    if package_names:
        print("│ The following packages will be upgraded:")
        for chunk_start in range(0, len(package_names), 8):
            chunk = package_names[chunk_start:chunk_start + 8]
            print("│   " + " ".join(chunk))

    if shutil.which("needrestart"):
        ok, out, _ = run_command(["needrestart", "-r", "l"], capture=True)
        if ok and out.strip():
            restarted, deferred, containers_message = parse_needrestart(out)
            print_status("•", "Restarting services...")
            if restarted:
                print("│   " + " ".join(restarted))
            else:
                print("│   No immediate service restarts required.")
            if deferred:
                print("│ Service restarts being deferred:")
                for item in deferred:
                    print(f"│   {item}")
            if containers_message:
                print(f"│ {containers_message}")
    if "failed" in upgrade_stdout.lower() or "error" in upgrade_stdout.lower():
        print_status("!", "Upgrade finished with warnings. Check verbose mode if needed.")
    else:
        print_status("✔", "Upgrade completed successfully.")


def update_system():
    title("System update")
    package_manager = detect_package_manager()
    if not package_manager:
        print_error("No supported package manager found on this system.")
        press_enter()
        return

    print_status("•", f"Detected package manager: {package_manager}")

    try:
        if package_manager == "apt":
            print_status("•", "Checking for updates...")
            ok, _, err = run_command(["apt", "update"], capture=True)
            if not ok:
                print_error(err.strip() or "Unable to refresh package lists.")
                press_enter()
                return

            ok, out, err = run_command(["apt", "list", "--upgradable"], capture=True)
            if not ok:
                print_error(err.strip() or "Unable to list upgradable packages.")
                press_enter()
                return

            packages = parse_apt_upgradable_lines(out)
            if not packages:
                print_status("✔", "System is already up to date.")
                press_enter()
                return

            print_status("•", f"Found {len(packages)} packages to upgrade.")
            print_status("•", "Upgrading packages...")
            ok, upgrade_out, upgrade_err = run_command(["apt", "upgrade", "-y"], capture=True)
            if not ok:
                print_error(upgrade_err.strip() or "Upgrade failed.")
                press_enter()
                return

            summarize_update_result(packages, upgrade_out, package_manager)
            print_status("✔", "System update completed successfully.")
            press_enter()
            return

        mapping = {
            "dnf": ["dnf", "upgrade", "--refresh", "-y"],
            "yum": ["yum", "update", "-y"],
            "pacman": ["pacman", "-Syu", "--noconfirm"],
            "zypper": ["zypper", "refresh"],
            "apk": ["apk", "update"],
        }
        print_status("•", "Running package manager update...")
        ok, out, err = run_command(mapping[package_manager], capture=True)
        if not ok:
            print_error(err.strip() or "Update failed.")
            press_enter()
            return
        print_status("✔", f"System update completed successfully with {package_manager}.")
        if VERBOSE and out.strip():
            print(out.strip())
        press_enter()
    except Exception as exc:
        print_error(str(exc))
        press_enter()


def update_systek():
    title("Systek self-update")
    install_dir = Path(INSTALL_PATH)
    if not (install_dir / ".git").exists():
        print_error("Installed copy is not a Git repository. Reinstall Systek from the repository to use self-update.")
        press_enter()
        return

    print_status("•", "Updating Systek from the official repository...")
    ok, out, err = run_command(["git", "-C", str(install_dir), "pull", REPO_URL, "main"], capture=True)
    if not ok:
        print_error(err.strip() or "Unable to update Systek.")
        press_enter()
        return

    print_status("✔", "Systek has been updated successfully.")
    if VERBOSE and out.strip():
        print(out.strip())
    print_status("•", "Relaunch Systek to use the latest version.")
    press_enter()


def remove_systek():
    title("Remove Systek")
    confirm = input("│ Are you sure you want to remove Systek ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Removal cancelled.")
        press_enter()
        return

    run_command(["rm", "-f", BIN_PATH], capture=True)
    run_command(["rm", "-rf", INSTALL_PATH], capture=True)
    print_status("✔", "Systek removal completed successfully.")
    press_enter()
    sys.exit(0)


def restart_service():
    title("Restart a service")
    service = input("│ Name of service to restart : ").strip()
    ok, _, err = run_command(["systemctl", "restart", service], capture=True)
    if ok:
        print_status("✔", f"Service {service} restarted successfully.")
    else:
        print_error(err.strip() or f"Failed to restart service {service}.")
    press_enter()


def restart_server():
    title("Server reboot")
    confirm = input("│ Are you sure you want to restart the server ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Server reboot cancelled.")
        press_enter()
        return
    print_status("•", "The server will restart now...")
    run_command(["sleep", "2"], capture=True)
    ok, _, err = run_command(["reboot"], capture=True)
    if not ok:
        print_error(err.strip() or "Server reboot failed.")
        press_enter()


def shutdown_server():
    title("Server shutdown")
    confirm = input("│ Are you sure you want to stop the server ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Server shutdown cancelled.")
        press_enter()
        return
    print_status("•", "The server will shut down now...")
    run_command(["sleep", "2"], capture=True)
    ok, _, err = run_command(["poweroff"], capture=True)
    if not ok:
        print_error(err.strip() or "Server shutdown failed.")
        press_enter()


def enable_service():
    title("Enable a service")
    service = input("│ Name of service to enable : ").strip()
    ok, _, err = run_command(["systemctl", "enable", service], capture=True)
    if ok:
        print_status("✔", f"Service {service} enabled successfully.")
    else:
        print_error(err.strip() or f"Failed to enable service {service}.")
    press_enter()


def disable_service():
    title("Disable a service")
    service = input("│ Name of service to disable : ").strip()
    ok, _, err = run_command(["systemctl", "disable", service], capture=True)
    if ok:
        print_status("✔", f"Service {service} disabled successfully.")
    else:
        print_error(err.strip() or f"Failed to disable service {service}.")
    press_enter()


def list_services():
    title("List of services")
    command_output(["systemctl", "list-units", "--type=service", "--no-pager"])


def monitor_service():
    title("Monitor a service")
    service = input("│ Name of the service to monitor (ex: cron.service) : ").strip()
    command_output(["systemctl", "status", service, "--no-pager"])


def check_resource_usage():
    title("Resource usage")
    command_output(["top", "-bn", "1"])


def check_disk_space():
    title("Disk space")
    command_output(["df", "-h"])


def check_network_connections():
    title("Network connections")
    if shutil.which("ss"):
        command_output(["ss", "-tunap"])
    else:
        command_output(["netstat", "-tunap"])


def check_memory_usage():
    title("RAM usage")
    ok, output, err = run_command(["free", "-m"], capture=True)
    if not ok:
        print_error(err.strip() or "Unable to read memory information.")
        press_enter()
        return

    lines = [line.split() for line in output.splitlines() if line.strip()]
    mem_line = next((line for line in lines if line[0].startswith("Mem:")), None)
    if not mem_line or len(mem_line) < 3:
        print_error("Memory information could not be parsed.")
        press_enter()
        return

    print(f"│ Total : {mem_line[1]} MB")
    print(f"│ Used  : {mem_line[2]} MB")
    print_status("✔", "RAM usage displayed successfully.")
    press_enter()


def check_cpu_usage():
    title("CPU usage")
    ok, output, err = run_command(["top", "-bn", "1"], capture=True)
    if not ok:
        print_error(err.strip() or "Unable to read CPU usage.")
        press_enter()
        return

    cpu_line = next((line for line in output.splitlines() if line.startswith("%Cpu") or line.startswith("%Cpu(s)")), "")
    match = re.search(r"(\d+[\.,]?\d*)\s*id", cpu_line)
    if match:
        idle = float(match.group(1).replace(",", "."))
        used = round(100 - idle, 2)
        print(f"│ CPU usage : {used}%")
        print_status("✔", "CPU usage displayed successfully.")
    else:
        print_error("CPU information could not be parsed.")
    press_enter()


def check_cpu_temperature():
    title("CPU temperature")
    if not shutil.which("sensors"):
        print_error("The 'sensors' command is not available. Install the 'lm-sensors' package.")
        press_enter()
        return
    command_output(["sensors"])


def mount_drive():
    title("Mount a drive")
    drive = input("│ Drive path : ").strip()
    mount_point = input("│ Mount point : ").strip()
    ok, _, err = run_command(["mount", drive, mount_point], capture=True)
    if ok:
        print_status("✔", f"Drive {drive} mounted successfully on {mount_point}.")
    else:
        print_error(err.strip() or "Mount failed.")
    press_enter()


def list_block_devices():
    title("Connected disks")
    command_output(["lsblk", "-fe7"])


def display_logs():
    title("Server logs")
    command_output(["journalctl", "-n", "100", "--no-pager"])


def save_logs():
    title("Back up server logs")
    destination = SCRIPT_DIR / "server_logs.log"
    ok, out, err = run_command(["journalctl", "-n", "500", "--no-pager"], capture=True)
    if not ok:
        print_error(err.strip() or "Unable to export server logs.")
        press_enter()
        return
    destination.write_text(out, encoding="utf-8")
    print_status("✔", f"Logs saved successfully to {destination}.")
    press_enter()


def install_package():
    title("Install a package")
    package_name = input("│ Package name to install : ").strip()
    package_manager = detect_package_manager()
    if not package_manager:
        print_error("No supported package manager found.")
        press_enter()
        return
    commands = {
        "apt": ["apt", "install", package_name, "-y"],
        "dnf": ["dnf", "install", package_name, "-y"],
        "yum": ["yum", "install", package_name, "-y"],
        "pacman": ["pacman", "-S", package_name, "--noconfirm"],
        "zypper": ["zypper", "install", "-y", package_name],
        "apk": ["apk", "add", package_name],
    }
    ok, _, err = run_command(commands[package_manager], capture=True)
    if ok:
        print_status("✔", f"Package {package_name} installed successfully.")
    else:
        print_error(err.strip() or f"Failed to install package {package_name}.")
    press_enter()


def remove_package():
    title("Remove a package")
    package_name = input("│ Package name to remove : ").strip()
    package_manager = detect_package_manager()
    if not package_manager:
        print_error("No supported package manager found.")
        press_enter()
        return
    commands = {
        "apt": ["apt", "remove", package_name, "-y"],
        "dnf": ["dnf", "remove", package_name, "-y"],
        "yum": ["yum", "remove", package_name, "-y"],
        "pacman": ["pacman", "-R", package_name, "--noconfirm"],
        "zypper": ["zypper", "remove", "-y", package_name],
        "apk": ["apk", "del", package_name],
    }
    ok, _, err = run_command(commands[package_manager], capture=True)
    if ok:
        print_status("✔", f"Package {package_name} removed successfully.")
    else:
        print_error(err.strip() or f"Failed to remove package {package_name}.")
    press_enter()


def check_ip_address():
    title("IP address")
    hostname = socket.gethostname()
    ip_address = get_local_ip()
    print(f"│ Hostname : {hostname}")
    print(f"│ IP       : {ip_address}")
    press_enter()


def ufw_status():
    title("Firewall status (ufw)")
    command_output(["ufw", "status"])


def enable_ufw():
    title("Enable the firewall (ufw)")
    confirm = input("│ Are you sure you want to enable the firewall (this may interrupt your SSH connection) ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Firewall enable cancelled.")
        press_enter()
        return
    ok, _, err = run_command(["ufw", "--force", "enable"], capture=True)
    if ok:
        print_status("✔", "Firewall enabled successfully.")
    else:
        print_error(err.strip() or "Failed to enable firewall.")
    press_enter()


def disable_ufw():
    title("Disable the firewall (ufw)")
    confirm = input("│ Are you sure you want to disable the firewall (this may interrupt your SSH connection) ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Firewall disable cancelled.")
        press_enter()
        return
    ok, _, err = run_command(["ufw", "disable"], capture=True)
    if ok:
        print_status("✔", "Firewall disabled successfully.")
    else:
        print_error(err.strip() or "Failed to disable firewall.")
    press_enter()


def add_ufw_rules():
    title("Add a firewall rule")
    rules = input("│ Which port do you want to allow (/tcp or /udp, leave blank for both) ? ").strip()
    confirm = input(f"│ Are you sure you want to open port {rules} ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Firewall rule addition cancelled.")
        press_enter()
        return
    ok, _, err = run_command(["ufw", "allow", rules], capture=True)
    if ok:
        print_status("✔", f"Firewall rule {rules} added successfully.")
    else:
        print_error(err.strip() or "Failed to add firewall rule.")
    press_enter()


def remove_ufw_rules():
    title("Remove a firewall rule")
    ok, out, _ = run_command(["ufw", "status", "numbered"], capture=True)
    if ok:
        print(out.strip())
    rules = input("│ Choose the rule number to delete : ").strip()
    confirm = input(f"│ Are you sure you want to delete rule {rules} ? (y/N) : ")
    if confirm.lower() not in {"y", "yes"}:
        print_status("•", "Firewall rule removal cancelled.")
        press_enter()
        return
    ok, _, err = run_command(["ufw", "--force", "delete", rules], capture=True)
    if ok:
        print_status("✔", f"Firewall rule {rules} removed successfully.")
    else:
        print_error(err.strip() or "Failed to remove firewall rule.")
    press_enter()


def install_cockpit():
    title("Install cockpit")
    package_manager = detect_package_manager()
    if package_manager != "apt":
        print_error("Cockpit installation is currently prepared for apt-based systems in this script.")
        press_enter()
        return
    ip_address = get_local_ip()
    ok, _, err = run_command(["apt", "install", "cockpit", "-y"], capture=True)
    if ok:
        print_status("✔", "Cockpit installed successfully.")
        print(f"│ Connect to https://{ip_address}:9090")
    else:
        print_error(err.strip() or "Cockpit installation failed.")
    press_enter()


def hold_package():
    title("Exclude a package from updates")
    package_name = input("│ Name of the package to exclude : ").strip()
    ok, _, err = run_command(["apt-mark", "hold", package_name], capture=True)
    if ok:
        print_status("✔", f"Package {package_name} excluded successfully.")
    else:
        print_error(err.strip() or f"Failed to exclude package {package_name}.")
    press_enter()


def unhold_package():
    title("Re-include a package in updates")
    package_name = input("│ Package name to re-include : ").strip()
    ok, _, err = run_command(["apt-mark", "unhold", package_name], capture=True)
    if ok:
        print_status("✔", f"Package {package_name} re-included successfully.")
    else:
        print_error(err.strip() or f"Failed to re-include package {package_name}.")
    press_enter()


def toggle_verbose():
    global VERBOSE
    VERBOSE = not VERBOSE
    title("Verbose mode")
    print_status("•", f"Verbose mode is now {'ON' if VERBOSE else 'OFF'}.")
    press_enter()


def print_menu():
    clear_screen()
    print(r'''
 ___  _  _  ___  ____  ____  _  _ 
/ __)( \/ )/ __)(_  _)( ___)( )/ )
\__ \ \  / \__ \  )(   )__)  )  ( 
(___/ (__) (___/ (__) (____)(_ )\_)
                    By Jonas52
│ 1  Update the system
│ 2  Add a package
│ 3  Delete a package
│ 4  Restart the server
│ 5  Stop the server
│ 6  Restart a service
│ 7  Activate a service
│ 8  Disable a service
│ 9  Show list of services
│ 10 Monitor a service
│ 11 Check resource usage
│ 12 Check disk space
│ 13 Check network connections
│ 14 Check IP address
│ 15 Check RAM usage
│ 16 Check CPU usage
│ 17 Check CPU temperature (not compatible with some VMs)
│ 18 Mount the disk
│ 19 List connected disks
│ 20 View server logs
│ 21 Back up server logs
│ 22 Display firewall parameters (ufw)
│ 23 Activate the firewall (ufw)
│ 24 Disable the firewall (ufw)
│ 25 Add a firewall rule
│ 26 Delete a firewall rule
│ 27 Install cockpit
│ 28 Exclude a package from updates
│ 29 Re-include a package in updates
│ u  Update Systek
│ r  Remove Systek
│ v  Toggle verbose mode
│ q or e Exit
╰──────────────────────────────────────────────────╼
''')
    print(f"│ Verbose mode : {'ON' if VERBOSE else 'OFF'}")
    print(f"│ Repository   : {REPO_URL}")
    print("╰──────────────────────────────────────────────────╼")


def execute_option(lang):
    try:
        match lang:
            case '1':
                update_system()
            case '2':
                install_package()
            case '3':
                remove_package()
            case '4':
                restart_server()
            case '5':
                shutdown_server()
            case '6':
                restart_service()
            case '7':
                enable_service()
            case '8':
                disable_service()
            case '9':
                list_services()
            case '10':
                monitor_service()
            case '11':
                check_resource_usage()
            case '12':
                check_disk_space()
            case '13':
                check_network_connections()
            case '14':
                check_ip_address()
            case '15':
                check_memory_usage()
            case '16':
                check_cpu_usage()
            case '17':
                check_cpu_temperature()
            case '18':
                mount_drive()
            case '19':
                list_block_devices()
            case '20':
                display_logs()
            case '21':
                save_logs()
            case '22':
                ufw_status()
            case '23':
                enable_ufw()
            case '24':
                disable_ufw()
            case '25':
                add_ufw_rules()
            case '26':
                remove_ufw_rules()
            case '27':
                install_cockpit()
            case '28':
                hold_package()
            case '29':
                unhold_package()
            case 'u' | 'U':
                update_systek()
            case 'r' | 'R':
                remove_systek()
            case 'v' | 'V':
                toggle_verbose()
            case '30' | 'EXIT' | 'exit' | 'e' | 'E' | 'Q' | 'q':
                clear_screen()
                raise SystemExit(0)
            case _:
                print("╰─╼ Invalid option. Please enter a valid number.")
                subprocess.call(['sleep', '1'])
    except SystemExit:
        raise
    except Exception as exc:
        print_error(str(exc))
        press_enter()


def main():
    require_root()

    parser = argparse.ArgumentParser(description="Systek Command Options")
    parser.add_argument('--update', action='store_true', help='Update Systek from the official Git repository')
    parser.add_argument('--remove', action='store_true', help='Remove Systek completely')
    parser.add_argument('--verbose', action='store_true', help='Show full command output')
    args, _ = parser.parse_known_args()

    global VERBOSE
    VERBOSE = args.verbose

    if args.update:
        update_systek()
        return
    if args.remove:
        remove_systek()
        return

    while True:
        clear_screen()
        print_menu()
        lang = input("├──╼ Choose an option : ")
        execute_option(lang)


if __name__ == "__main__":
    main()

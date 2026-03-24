#!/usr/bin/env python3
import argparse
import os
import pwd
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

APP_NAME = "systek"
INSTALL_PATH = Path("/opt/systek")
BIN_PATH = Path(f"/usr/local/bin/{APP_NAME}")
REPO_URL = "https://github.com/jonas52/systek.git"
REPO_WEB_URL = "https://github.com/jonas52/systek/"
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_META_PATH = INSTALL_PATH / ".systek-repo-url"
AUTOSTART_MARKER_START = "# >>> systek autostart >>>"
AUTOSTART_MARKER_END = "# <<< systek autostart <<<"


if sys.version_info < (3, 10):
    print("╰─╼ This script requires Python 3.10 or later.")
    sys.exit(1)


def clear_screen() -> None:
    os.system("clear")


def pause() -> None:
    input("╰─╼ Press Enter to continue...")


def run_command(cmd: list[str], *, check: bool = True, capture: bool = False, text: bool = True):
    return subprocess.run(cmd, check=check, capture_output=capture, text=text)


def require_root() -> None:
    if os.geteuid() != 0:
        print("╰─╼ This script must be run as superuser (root).")
        sys.exit(1)


parser = argparse.ArgumentParser(description="Systek command options")
parser.add_argument("--update", action="store_true", help="Update Systek from GitHub")
parser.add_argument("--remove", action="store_true", help="Remove Systek from this machine")
parser.add_argument("--enable-autostart", action="store_true", help="Enable Systek at shell session start")
parser.add_argument("--disable-autostart", action="store_true", help="Disable Systek autostart")
args, _ = parser.parse_known_args()


def print_header(title: str) -> None:
    clear_screen()
    print(r"""
  ____            _       _    
 / ___| _   _ ___| |_ ___| | __
 \___ \| | | / __| __/ _ \ |/ /
  ___) | |_| \__ \ ||  __/   < 
 |____/ \__, |___/\__\___|_|\_\
        |___/                  
""")
    print(f"│ {title}")
    print("╰──────────────────────────────────────────────────╼")


def get_repo_url() -> str:
    if REPO_META_PATH.exists():
        value = REPO_META_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    return REPO_URL


def sync_local_install_from_repo(repo_path: Path) -> None:
    for entry in list(INSTALL_PATH.iterdir()):
        if entry.name in {".git", ".systek-repo-url", "__pycache__"}:
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()

    for entry in repo_path.iterdir():
        if entry.name == ".git":
            continue
        target = INSTALL_PATH / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, target)

    shutil.copytree(repo_path / ".git", INSTALL_PATH / ".git", dirs_exist_ok=True)
    REPO_META_PATH.write_text(get_repo_url() + "\n", encoding="utf-8")
    (INSTALL_PATH / "systek.py").chmod(0o755)


def update_from_fresh_clone(repo_url: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="systek-update-") as tmpdir:
        tmp_path = Path(tmpdir) / "repo"
        clone = run_command(["git", "clone", "--depth", "1", repo_url, str(tmp_path)], check=False, capture=True)
        if clone.returncode != 0:
            error = clone.stderr.strip().splitlines()[-1] if clone.stderr else "Unable to clone repository."
            return False, error
        INSTALL_PATH.mkdir(parents=True, exist_ok=True)
        sync_local_install_from_repo(tmp_path)
    return True, "Updated from repository snapshot."


def get_target_user() -> str:
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"


def get_user_home(username: str) -> Path:
    return Path(pwd.getpwnam(username).pw_dir)


def build_autostart_block() -> str:
    return f"""{AUTOSTART_MARKER_START}
if [ -z "${{SYSTEK_AUTOSTART_DONE:-}}" ] && command -v systek >/dev/null 2>&1; then
    export SYSTEK_AUTOSTART_DONE=1
    if [ "$(id -u)" -eq 0 ]; then
        systek
    elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        sudo systek
    fi
fi
{AUTOSTART_MARKER_END}
"""


def ensure_autostart_in_file(shell_rc: Path) -> bool:
    content = shell_rc.read_text(encoding="utf-8") if shell_rc.exists() else ""
    if AUTOSTART_MARKER_START in content:
        return False
    if content and not content.endswith("\n"):
        content += "\n"
    content += build_autostart_block()
    shell_rc.write_text(content, encoding="utf-8")
    return True


def remove_autostart_from_file(shell_rc: Path) -> bool:
    if not shell_rc.exists():
        return False
    content = shell_rc.read_text(encoding="utf-8")
    if AUTOSTART_MARKER_START not in content:
        return False
    start = content.index(AUTOSTART_MARKER_START)
    end = content.index(AUTOSTART_MARKER_END) + len(AUTOSTART_MARKER_END)
    if end < len(content) and content[end:end+1] == "\n":
        end += 1
    new_content = content[:start] + content[end:]
    shell_rc.write_text(new_content, encoding="utf-8")
    return True


def enable_autostart() -> None:
    require_root()
    print_header("Enable Systek at session start")
    user = get_target_user()
    try:
        home = get_user_home(user)
    except KeyError:
        print(f"│ Could not resolve the home directory for user '{user}'.")
        pause()
        return

    changed = []
    for name in (".bashrc", ".zshrc"):
        rc = home / name
        if ensure_autostart_in_file(rc):
            changed.append(str(rc))

    if changed:
        print(f"│ Autostart enabled for user : {user}")
        for item in changed:
            print(f"│ Updated : {item}")
        print("│ Systek will start automatically on the next shell session.")
        print("│ Note : it will run automatically only if root access is already available")
        print("│        or passwordless sudo is configured for that session.")
    else:
        print(f"│ Autostart is already enabled for user : {user}")
    pause()


def disable_autostart() -> None:
    require_root()
    print_header("Disable Systek autostart")
    user = get_target_user()
    try:
        home = get_user_home(user)
    except KeyError:
        print(f"│ Could not resolve the home directory for user '{user}'.")
        pause()
        return

    changed = []
    for name in (".bashrc", ".zshrc"):
        rc = home / name
        if remove_autostart_from_file(rc):
            changed.append(str(rc))

    if changed:
        print(f"│ Autostart disabled for user : {user}")
        for item in changed:
            print(f"│ Updated : {item}")
    else:
        print(f"│ No autostart block was found for user : {user}")
    pause()


def update_systek() -> None:
    require_root()
    print_header("Updating Systek")

    git_dir = INSTALL_PATH / ".git"
    if not git_dir.exists():
        print("│ Installation is not a Git checkout. Update is unavailable.")
        pause()
        return

    try:
        print(f"│ Repository : {REPO_URL}")
        run_command(["git", "-C", str(INSTALL_PATH), "remote", "set-url", "origin", REPO_URL])
        run_command(["git", "-C", str(INSTALL_PATH), "fetch", "origin"])
        result = run_command(["git", "-C", str(INSTALL_PATH), "pull", "--ff-only", "origin", "main"], capture=True)
        print("│ Update completed successfully.")
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[-6:]:
                print(f"│ {line}")
        print(f"│ Launch with: {BIN_PATH}")
    except subprocess.CalledProcessError as exc:
        print(f"│ Update failed: {exc}")
    pause()


def remove_systek() -> None:
    require_root()
    print_header("Removing Systek")
    confirm = input("│ Are you sure you want to remove Systek? (y/N) : ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("│ Removal cancelled.")
        pause()
        return

    try:
        if BIN_PATH.exists() or BIN_PATH.is_symlink():
            BIN_PATH.unlink()
        if INSTALL_PATH.exists():
            shutil.rmtree(INSTALL_PATH)
        print("│ Systek has been removed.")
    except Exception as exc:
        print(f"│ Removal failed: {exc}")
    pause()


if args.update:
    update_systek()
    sys.exit(0)

if args.remove:
    remove_systek()
    sys.exit(0)

if args.enable_autostart:
    enable_autostart()
    sys.exit(0)

if args.disable_autostart:
    disable_autostart()
    sys.exit(0)

require_root()


def restart_service() -> None:
    print_header("Restart a service")
    service = input("│ Service name to restart : ").strip()
    try:
        run_command(["systemctl", "restart", service])
        print(f"│ Service '{service}' restarted successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to restart '{service}': {exc}")
    pause()


def restart_server() -> None:
    print_header("Reboot server")
    confirm = input("│ Are you sure you want to reboot the server? (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        print("│ The server will reboot in 2 seconds.")
        try:
            run_command(["sleep", "2"])
            run_command(["reboot"])
        except subprocess.CalledProcessError as exc:
            print(f"│ Reboot failed: {exc}")
            pause()
    else:
        print("│ Reboot cancelled.")
        pause()


def shutdown_server() -> None:
    print_header("Shutdown server")
    confirm = input("│ Are you sure you want to power off the server? (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        print("│ The server will power off in 2 seconds.")
        try:
            run_command(["sleep", "2"])
            run_command(["poweroff"])
        except subprocess.CalledProcessError as exc:
            print(f"│ Shutdown failed: {exc}")
            pause()
    else:
        print("│ Shutdown cancelled.")
        pause()


def update_system() -> None:
    print_header("System update")
    package_managers = {
        "apt-get": [["apt-get", "update"], ["apt-get", "upgrade", "-y"]],
        "dnf": [["dnf", "upgrade", "--refresh", "-y"]],
        "yum": [["yum", "update", "-y"]],
        "pacman": [["pacman", "-Syu", "--noconfirm"]],
        "zypper": [["zypper", "refresh"], ["zypper", "update", "-y"]],
        "apk": [["apk", "update"], ["apk", "upgrade"]],
    }

    for pm, commands in package_managers.items():
        if shutil.which(pm):
            try:
                for cmd in commands:
                    run_command(cmd)
                print(f"│ System update completed successfully with {pm}.")
                pause()
                return
            except subprocess.CalledProcessError as exc:
                print(f"│ System update failed with {pm}: {exc}")
                pause()
                return

    print("│ No supported package manager was found on this system.")
    pause()



def enable_service() -> None:
    print_header("Enable a service")
    service = input("│ Service name to enable : ").strip()
    try:
        run_command(["systemctl", "enable", service])
        print(f"│ Service '{service}' enabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to enable '{service}': {exc}")
    pause()



def disable_service() -> None:
    print_header("Disable a service")
    service = input("│ Service name to disable : ").strip()
    try:
        run_command(["systemctl", "disable", service])
        print(f"│ Service '{service}' disabled successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to disable '{service}': {exc}")
    pause()



def list_services() -> None:
    print_header("List of services")
    try:
        run_command(["systemctl", "list-units", "--type=service", "--no-pager"])
        print("│ Service listing completed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to list services: {exc}")
    pause()



def monitor_service() -> None:
    print_header("Monitor a service")
    service = input("│ Service name to monitor (example: cron.service) : ").strip()
    try:
        run_command(["systemctl", "status", service, "--no-pager"])
        print(f"│ Service status for '{service}' displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display service status: {exc}")
    pause()



def check_resource_usage() -> None:
    print_header("Resource usage")
    try:
        run_command(["top"])
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display resource usage: {exc}")
        pause()



def check_disk_space() -> None:
    print_header("Disk space")
    try:
        run_command(["df", "-h"])
        print("│ Disk space check completed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to check disk space: {exc}")
    pause()



def check_network_connections() -> None:
    print_header("Network connections")
    command = None
    if shutil.which("ss"):
        command = ["ss", "-tunap"]
    elif shutil.which("netstat"):
        command = ["netstat", "-tunap"]

    if not command:
        print("│ Neither 'ss' nor 'netstat' is available on this system.")
        pause()
        return

    try:
        run_command(command)
        print("│ Network connection check completed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to check network connections: {exc}")
    pause()



def check_memory_usage() -> None:
    print_header("RAM usage")
    result = run_command(["free", "-m"], check=False, capture=True)
    if result.returncode == 0:
        print(result.stdout)
        print("│ RAM usage displayed successfully.")
    else:
        print(f"│ Failed to display RAM usage: {result.stderr}")
    pause()



def check_cpu_usage() -> None:
    print_header("CPU usage")
    result = run_command(["top", "-bn", "1"], check=False, capture=True)
    if result.returncode == 0:
        cpu_line = next((line for line in result.stdout.splitlines() if line.startswith("%Cpu(s)") or line.lower().startswith("cpu(s)")), None)
        if cpu_line:
            print(f"│ {cpu_line}")
        else:
            print(result.stdout)
        print("│ CPU usage displayed successfully.")
    else:
        print(f"│ Failed to display CPU usage: {result.stderr}")
    pause()



def check_cpu_temperature() -> None:
    print_header("CPU temperature")
    if not shutil.which("sensors"):
        print("│ The 'sensors' command is not available. Install the 'lm-sensors' package.")
        pause()
        return
    result = run_command(["sensors"], check=False, capture=True)
    if result.returncode == 0:
        print(result.stdout)
        print("│ CPU temperature displayed successfully.")
    else:
        print(f"│ Failed to display CPU temperature: {result.stderr}")
    pause()



def mount_drive() -> None:
    print_header("Mount a drive")
    drive = input("│ Drive path : ").strip()
    mount_point = input("│ Mount point : ").strip()
    result = run_command(["mount", drive, mount_point], check=False, capture=True)
    if result.returncode == 0:
        print("│ Drive mounted successfully.")
    else:
        print(f"│ Failed to mount drive: {result.stderr}")
    pause()



def list_block_devices() -> None:
    print_header("Connected disks")
    result = run_command(["lsblk", "-fe7"], check=False, capture=True)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"│ Failed to list block devices: {result.stderr}")
    pause()



def display_logs() -> None:
    print_header("Live server logs")
    print("│ Press Ctrl+C to stop log streaming.")
    try:
        subprocess.run(["tail", "-f", "/var/log/syslog"])
    except KeyboardInterrupt:
        pass
    pause()



def save_logs() -> None:
    print_header("Backup server logs")
    output_path = SCRIPT_DIR / "server_logs.log"
    result = run_command(["journalctl", "-n", "500", "--no-pager"], check=False, capture=True)
    if result.returncode == 0:
        output_path.write_text(result.stdout, encoding="utf-8")
        print(f"│ Logs saved to: {output_path}")
    else:
        print("│ journalctl is unavailable, trying /var/log/syslog...")
        try:
            syslog_path = Path("/var/log/syslog")
            output_path.write_text(syslog_path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            print(f"│ Logs saved to: {output_path}")
        except Exception as exc:
            print(f"│ Failed to save logs: {exc}")
    pause()



def add_package() -> None:
    print_header("Install a package")
    package = input("│ Package name to install : ").strip()
    try:
        run_command(["apt", "install", package, "-y"])
        print(f"│ Package '{package}' installed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to install package: {exc}")
    pause()



def remove_package() -> None:
    print_header("Remove a package")
    package = input("│ Package name to remove : ").strip()
    try:
        run_command(["apt", "remove", package, "-y"])
        print(f"│ Package '{package}' removed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to remove package: {exc}")
    pause()



def get_primary_ip() -> str | None:
    try:
        result = run_command(["hostname", "-I"], check=False, capture=True)
        if result.returncode == 0:
            addresses = [part for part in result.stdout.split() if "." in part and not part.startswith("127.")]
            if addresses:
                return addresses[0]
    except Exception:
        pass

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        address = sock.getsockname()[0]
        sock.close()
        return address
    except Exception:
        return None



def check_ip_address() -> None:
    print_header("Host and IP address")
    hostname = socket.gethostname()
    ip_address = get_primary_ip()
    print(f"│ Hostname   : {hostname}")
    if ip_address:
        print(f"│ IP address : {ip_address}")
    else:
        print("│ No IP address could be detected.")
    pause()



def ufw_status() -> None:
    print_header("UFW firewall status")
    try:
        run_command(["ufw", "status"])
        print("│ Firewall status displayed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to display UFW status: {exc}")
    except FileNotFoundError:
        print("│ The 'ufw' command is not available on this system.")
    pause()



def enable_ufw() -> None:
    print_header("Enable UFW firewall")
    confirm = input("│ Are you sure you want to enable UFW? This may interrupt SSH access. (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        try:
            run_command(["ufw", "enable"])
            print("│ UFW enabled successfully.")
        except subprocess.CalledProcessError as exc:
            print(f"│ Failed to enable UFW: {exc}")
        except FileNotFoundError:
            print("│ The 'ufw' command is not available on this system.")
    else:
        print("│ UFW enable cancelled.")
    pause()



def disable_ufw() -> None:
    print_header("Disable UFW firewall")
    confirm = input("│ Are you sure you want to disable UFW? This may interrupt SSH access. (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        try:
            run_command(["ufw", "disable"])
            print("│ UFW disabled successfully.")
        except subprocess.CalledProcessError as exc:
            print(f"│ Failed to disable UFW: {exc}")
        except FileNotFoundError:
            print("│ The 'ufw' command is not available on this system.")
    else:
        print("│ UFW disable cancelled.")
    pause()



def add_ufw_rules() -> None:
    print_header("Add a firewall rule")
    rule = input("│ Port/service to allow (example: 22/tcp) : ").strip()
    confirm = input(f"│ Are you sure you want to open '{rule}'? (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        try:
            run_command(["ufw", "allow", rule])
            print(f"│ Rule '{rule}' added successfully.")
        except subprocess.CalledProcessError as exc:
            print(f"│ Failed to add firewall rule: {exc}")
        except FileNotFoundError:
            print("│ The 'ufw' command is not available on this system.")
    else:
        print("│ Rule addition cancelled.")
    pause()



def remove_ufw_rules() -> None:
    print_header("Remove a firewall rule")
    try:
        run_command(["ufw", "status", "numbered"])
    except Exception:
        pass
    rule = input("│ Rule number or rule value to delete : ").strip()
    confirm = input(f"│ Are you sure you want to delete '{rule}'? (y/N) : ").strip().lower()
    if confirm in {"y", "yes"}:
        try:
            run_command(["ufw", "delete", rule])
            print(f"│ Rule '{rule}' deleted successfully.")
        except subprocess.CalledProcessError as exc:
            print(f"│ Failed to delete firewall rule: {exc}")
        except FileNotFoundError:
            print("│ The 'ufw' command is not available on this system.")
    else:
        print("│ Rule deletion cancelled.")
    pause()



def install_cockpit() -> None:
    print_header("Install Cockpit")
    ip_address = get_primary_ip() or "<server-ip>"
    try:
        run_command(["apt", "install", "cockpit", "-y"])
        print("│ Cockpit installed successfully.")
        print(f"│ Open : https://{ip_address}:9090")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to install Cockpit: {exc}")
    pause()



def hold_package() -> None:
    print_header("Hold a package")
    package = input("│ Package name to hold : ").strip()
    try:
        run_command(["apt-mark", "hold", package])
        print(f"│ Package '{package}' is now held.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to hold package: {exc}")
    pause()



def unhold_package() -> None:
    print_header("Unhold a package")
    package = input("│ Package name to unhold : ").strip()
    try:
        run_command(["apt-mark", "unhold", package])
        print(f"│ Package '{package}' is no longer held.")
    except subprocess.CalledProcessError as exc:
        print(f"│ Failed to unhold package: {exc}")
    pause()



def print_menu() -> None:
    print_header("Linux administration menu")
    print(r"""
│  1  Update the system
│  2  Install a package
│  3  Remove a package
│  4  Reboot the server
│  5  Power off the server
│  6  Restart a service
│  7  Enable a service
│  8  Disable a service
│  9  List services
│ 10  Monitor a service
│ 11  Check resource usage
│ 12  Check disk space
│ 13  Check network connections
│ 14  Check host and IP address
│ 15  Check RAM usage
│ 16  Check CPU usage
│ 17  Check CPU temperature
│ 18  Mount a drive
│ 19  List connected disks
│ 20  View live server logs
│ 21  Backup server logs
│ 22  Show UFW firewall status
│ 23  Enable UFW firewall
│ 24  Disable UFW firewall
│ 25  Add a firewall rule
│ 26  Remove a firewall rule
│ 27  Install Cockpit
│ 28  Hold a package
│ 29  Unhold a package
│  u  Update Systek
│  a  Enable autostart at session login
│  x  Disable autostart
│  r  Remove Systek
│  q  Exit
╰──────────────────────────────────────────────────╼
""")


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
    "U": update_systek,
    "a": enable_autostart,
    "A": enable_autostart,
    "x": disable_autostart,
    "X": disable_autostart,
    "r": remove_systek,
    "R": remove_systek,
}


while True:
    print_menu()
    choice = input("├──╼ Choose an option : ").strip()
    if choice.lower() in {"q", "e", "exit"}:
        clear_screen()
        break
    action = ACTIONS.get(choice)
    if action is None:
        print("╰─╼ Invalid option. Please enter a valid choice.")
        subprocess.call(["sleep", "1"])
        continue
    try:
        action()
    except KeyboardInterrupt:
        print("\n│ Action cancelled.")
        pause()
    except Exception as exc:
        print(f"│ An error occurred: {exc}")
        pause()

clear_screen()

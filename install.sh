#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/jonas52/systek.git"
REPO_WEB_URL="https://github.com/jonas52/systek/"
INSTALL_DIR="/opt/systek"
ENTRY_POINT="systek.py"
SYMLINK_PATH="/usr/local/bin/systek"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$EUID" -ne 0 ]]; then
    echo "╰─╼ This script must be run as superuser (root)."
    exit 1
fi

if command -v apt >/dev/null 2>&1; then
    echo "│ Installing dependencies with apt..."
    apt update >/dev/null 2>&1
    apt install -y git python3 python3-pip python3-netifaces >/dev/null 2>&1
elif command -v dnf >/dev/null 2>&1; then
    echo "│ Installing dependencies with dnf..."
    dnf install -y git python3 python3-pip >/dev/null 2>&1
elif command -v yum >/dev/null 2>&1; then
    echo "│ Installing dependencies with yum..."
    yum install -y git python3 python3-pip >/dev/null 2>&1
elif command -v pacman >/dev/null 2>&1; then
    echo "│ Installing dependencies with pacman..."
    pacman -Sy --noconfirm git python python-pip >/dev/null 2>&1
else
    echo "╰─╼ Unsupported package manager. Install Git and Python manually, then rerun this script."
    exit 1
fi

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

echo "│ Installing Systek..."
cp "$SCRIPT_DIR/$ENTRY_POINT" "$INSTALL_DIR/$ENTRY_POINT"
[[ -f "$SCRIPT_DIR/README.md" ]] && cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/README.md"
echo "$REPO_URL" > "$INSTALL_DIR/.systek-repo-url"
chmod +x "$INSTALL_DIR/$ENTRY_POINT"
ln -sf "$INSTALL_DIR/$ENTRY_POINT" "$SYMLINK_PATH"

echo "│ Installation completed successfully."
echo "│ Launch with : systek"
echo "│ Update with : sudo systek --update"
echo "│ Enable autostart : sudo systek --enable-autostart"
echo "╰─╼ Remove with : sudo systek --remove"

#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="systek"
INSTALL_DIR="/opt/systek"
SYMLINK_PATH="/usr/local/bin/systek"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$EUID" -ne 0 ]]; then
  echo "╰─╼ This script must be run as superuser (root)."
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y git python3 python3-pip
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y git python3 python3-pip
elif command -v yum >/dev/null 2>&1; then
  yum install -y git python3 python3-pip
elif command -v pacman >/dev/null 2>&1; then
  pacman -Sy --noconfirm git python python-pip
else
  echo "╰─╼ Unsupported package manager. Install Python and Git manually."
  exit 1
fi

mkdir -p "$INSTALL_DIR"
rsync -a --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$SCRIPT_DIR/" "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/systek.py"
ln -sf "$INSTALL_DIR/systek.py" "$SYMLINK_PATH"

echo "╰─╼ Installation complete. Use 'systek', 'systek --update' or 'systek --remove'."

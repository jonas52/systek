#!/usr/bin/env bash
set -euo pipefail
APP_NAME="systek"
INSTALL_DIR="/opt/systek"
BIN_LINK="/usr/local/bin/systek"
VENV_DIR="$INSTALL_DIR/.venv"
REPO_URL="https://github.com/jonas52/systek.git"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
  echo "Exemple : curl -fsSL https://raw.githubusercontent.com/jonas52/systek/main/install.sh | sudo bash"
  exit 1
fi

detect_pkg_manager() {
  if command -v apt >/dev/null 2>&1; then echo "apt"; return; fi
  if command -v dnf >/dev/null 2>&1; then echo "dnf"; return; fi
  if command -v yum >/dev/null 2>&1; then echo "yum"; return; fi
  if command -v pacman >/dev/null 2>&1; then echo "pacman"; return; fi
  echo "unsupported"
}

install_deps() {
  case "$1" in
    apt) apt update && apt install -y git python3 python3-venv python3-pip curl ;;
    dnf) dnf install -y git python3 python3-pip curl ;;
    yum) yum install -y git python3 python3-pip curl ;;
    pacman) pacman -Sy --noconfirm git python python-pip curl ;;
  esac
}

PKG_MANAGER="$(detect_pkg_manager)"
[[ "$PKG_MANAGER" == "unsupported" ]] && { echo "Gestionnaire non supporté"; exit 1; }

echo "[1/5] Dépendances..."
install_deps "$PKG_MANAGER"

echo "[2/5] Installation du dépôt..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull origin main
else
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo "[3/5] Virtualenv..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install -e "$INSTALL_DIR"

echo "[4/5] Lanceur global..."
cat > "$BIN_LINK" <<LAUNCHER
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m systek "\$@"
LAUNCHER
chmod +x "$BIN_LINK"

echo "[5/5] Répertoires système..."
mkdir -p /etc/systek /var/log/systek /var/lib/systek

echo
echo "Installation terminée."
echo "Commande standard : systek"
echo "Commande admin    : sudo systek"
echo "Sans sudo, certaines fonctionnalités seront limitées."

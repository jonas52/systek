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

PKG_MANAGER="$(detect_pkg_manager)"

if [[ "$PKG_MANAGER" == "unsupported" ]]; then
  echo "Gestionnaire de paquets non supporté."
  exit 1
fi

install_deps() {
  case "$PKG_MANAGER" in
    apt)
      apt update
      apt install -y git python3 python3-venv python3-pip curl
      ;;
    dnf)
      dnf install -y git python3 python3-pip
      python3 -m ensurepip --upgrade || true
      ;;
    yum)
      yum install -y git python3 python3-pip
      ;;
    pacman)
      pacman -Sy --noconfirm git python python-pip
      ;;
  esac
}

echo "[1/5] Installation des dépendances..."
install_deps

echo "[2/5] Installation dans $INSTALL_DIR..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull origin main
else
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo "[3/5] Création du virtualenv..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install -e "$INSTALL_DIR"

echo "[4/5] Création du lanceur global..."
cat > "$BIN_LINK" <<LAUNCHER
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m systek "\$@"
LAUNCHER
chmod +x "$BIN_LINK"

echo "[5/5] Préparation des dossiers système..."
mkdir -p /etc/systek /var/log/systek /var/lib/systek
cp -f "$INSTALL_DIR/uninstall.sh" /opt/systek/uninstall.sh
chmod +x /opt/systek/uninstall.sh

echo

echo "Installation terminée."
echo
echo "Lancement normal       : systek"
echo "Lancement admin complet: sudo systek"
echo
echo "Sans sudo, certaines fonctionnalités seront limitées."

#!/usr/bin/env bash
set -euo pipefail

APP_NAME="systek"
INSTALL_DIR="/opt/systek"
BIN_LINK="/usr/local/bin/systek"
VENV_DIR="$INSTALL_DIR/.venv"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
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
  local pkg="$1"
  case "$pkg" in
    apt)
      apt update
      apt install -y python3 python3-venv python3-pip git curl
      ;;
    dnf)
      dnf install -y python3 python3-pip git curl
      python3 -m ensurepip --upgrade || true
      ;;
    yum)
      yum install -y python3 python3-pip git curl
      ;;
    pacman)
      pacman -Sy --noconfirm python python-pip git curl
      ;;
    *)
      echo "Gestionnaire de paquets non supporté."
      exit 1
      ;;
  esac
}

PKG_MANAGER="$(detect_pkg_manager)"
install_deps "$PKG_MANAGER"

mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

cat > "$BIN_LINK" <<LAUNCHER
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m systek "\$@"
LAUNCHER
chmod +x "$BIN_LINK"
mkdir -p /etc/systek /var/log/systek /var/lib/systek

echo
echo "Installation terminée."
echo "Lancement utilisateur : systek"
echo "Lancement admin complet : sudo systek"
echo "Sans sudo, certaines fonctionnalités sont limitées."

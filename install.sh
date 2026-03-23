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
  if command -v zypper >/dev/null 2>&1; then echo "zypper"; return; fi
  if command -v apk >/dev/null 2>&1; then echo "apk"; return; fi
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
      apt install -y python3 python3-venv python3-pip
      ;;
    dnf)
      dnf install -y python3 python3-pip
      python3 -m ensurepip --upgrade || true
      ;;
    yum)
      yum install -y python3 python3-pip
      ;;
    pacman)
      pacman -Sy --noconfirm python python-pip
      ;;
    zypper)
      zypper install -y python3 python3-pip python3-virtualenv
      ;;
    apk)
      apk add python3 py3-pip
      ;;
  esac
}

echo "[1/4] Dépendances système..."
install_deps

echo "[2/4] Copie de l'application..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

echo "[3/4] Virtualenv Python..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install "$INSTALL_DIR"

echo "[4/4] Lanceur global..."
cat > "$BIN_LINK" <<SCRIPT
#!/usr/bin/env bash
exec "$VENV_DIR/bin/systek" "\$@"
SCRIPT
chmod +x "$BIN_LINK"

mkdir -p /etc/systek /var/log/systek /var/lib/systek

echo

echo "Installation terminée."
echo "Lancer: systek"
echo "Mode complet: sudo systek"
echo "Sans sudo certaines fonctionnalités sont limitées."

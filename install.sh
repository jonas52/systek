#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/systek"
BIN_LINK="/usr/local/bin/systek"
VENV_DIR="$INSTALL_DIR/.venv"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
  exit 1
fi

if [[ ! -f "$SCRIPT_DIR/requirements.txt" || ! -f "$SCRIPT_DIR/pyproject.toml" ]]; then
  echo "Projet incomplet : requirements.txt ou pyproject.toml introuvable dans $SCRIPT_DIR" >&2
  exit 1
fi

if command -v apt >/dev/null 2>&1; then
  echo "[1/4] Dépendances système..."
  apt update
  apt install -y python3 python3-venv python3-pip
elif command -v dnf >/dev/null 2>&1; then
  echo "[1/4] Dépendances système..."
  dnf install -y python3 python3-pip
elif command -v yum >/dev/null 2>&1; then
  echo "[1/4] Dépendances système..."
  yum install -y python3 python3-pip
elif command -v pacman >/dev/null 2>&1; then
  echo "[1/4] Dépendances système..."
  pacman -Sy --noconfirm python python-pip
else
  echo "Gestionnaire de paquets non supporté." >&2
  exit 1
fi

echo "[2/4] Copie de l'application..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -a "$SCRIPT_DIR"/. "$INSTALL_DIR"/
find "$INSTALL_DIR" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' \) -prune -exec rm -rf {} +
rm -rf "$INSTALL_DIR/.venv"

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
echo "Lancer : systek"
echo "Mode complet : sudo systek"
echo "Sans sudo certaines fonctionnalités sont limitées."

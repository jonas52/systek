#!/usr/bin/env bash
set -euo pipefail

APP_NAME="systek"
INSTALL_DIR="/opt/systek"
BIN_LINK="/usr/local/bin/systek"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
  echo "This installer must be run as root."
  exit 1
fi

echo "[1/4] System dependencies..."
apt update >/dev/null
apt install -y git python3 python3-pip iproute2 net-tools lm-sensors >/dev/null

echo "[2/4] Installing application..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/systek.py" "$INSTALL_DIR/systek.py"
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/README.md"
chmod +x "$INSTALL_DIR/systek.py"

echo "[3/4] Creating launcher..."
cat > "$BIN_LINK" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/systek.py" "\$@"
EOF
chmod +x "$BIN_LINK"

echo "[4/4] Done"
echo "Run: sudo systek"

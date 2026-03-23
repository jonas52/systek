#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/systek"
BIN_LINK="/usr/local/bin/systek"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
  exit 1
fi

read -r -p "Confirmer la suppression de Systek ? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  echo "Annulé."
  exit 0
fi

rm -f "$BIN_LINK"
rm -rf "$INSTALL_DIR"
read -r -p "Supprimer aussi /etc/systek, /var/log/systek, /var/lib/systek ? [y/N] " PURGE
if [[ "$PURGE" =~ ^([yY][eE][sS]|[yY])$ ]]; then
  rm -rf /etc/systek /var/log/systek /var/lib/systek
fi

echo "Systek a été désinstallé."

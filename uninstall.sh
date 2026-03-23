#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
  exit 1
fi

read -r -p "Supprimer Systek ? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^([yY]|yes|YES)$ ]]; then
  echo "Annulé."
  exit 0
fi

rm -f /usr/local/bin/systek
rm -rf /opt/systek

read -r -p "Supprimer aussi /etc/systek /var/log/systek /var/lib/systek ? [y/N] " PURGE
if [[ "$PURGE" =~ ^([yY]|yes|YES)$ ]]; then
  rm -rf /etc/systek /var/log/systek /var/lib/systek
fi

echo "Systek a été désinstallé."

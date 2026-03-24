#!/usr/bin/env bash
set -euo pipefail
if [[ "${EUID}" -ne 0 ]]; then
  echo "Ce script doit être lancé avec sudo/root."
  exit 1
fi
rm -f /usr/local/bin/systek
rm -rf /opt/systek
echo "Systek supprimé."

#!/usr/bin/env bash
set -euo pipefail

echo "== Systek doctor =="
for cmd in python3 git systemctl journalctl; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd"
  else
    echo "[KO] $cmd"
  fi
done

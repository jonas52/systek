# Systek

Systek is a Linux system administration TUI with a professional layout inspired by btop for monitoring, while keeping a straightforward operator workflow.

## Highlights

- Professional and simple admin-oriented layout
- Live CPU / RAM / Disk / Network / Load monitoring
- Actions grouped by categories
- Read-only mode without sudo
- Full administration mode with sudo
- Install, update and uninstall included

## Install

```bash
sudo ./install.sh
```

## Run

```bash
systek
sudo systek
```

Without sudo, some administrative actions are limited.

## Keys

- `↑` / `↓`: move in actions
- `tab`: change focus between categories and actions
- `enter`: run selected action
- `/`: focus command bar
- `r`: refresh dashboard
- `q`: quit

## Commands in the command bar

Examples:

```text
20
9 nginx
4 htop
24 /dev/sdb1 /mnt/data
31 22/tcp
```

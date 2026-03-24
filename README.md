<div align="center">

# Systek

<pre>
███████╗██╗   ██╗███████╗████████╗███████╗██╗  ██╗
██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝██║ ██╔╝
███████╗ ╚████╔╝ ███████╗   ██║   █████╗  █████╔╝ 
╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██╔═██╗ 
███████║   ██║   ███████║   ██║   ███████╗██║  ██╗
╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
</pre>

<p>
  <strong>Linux terminal administration menu</strong><br>
  Fast, readable, and built for everyday server management.
</p>

<p>
  <a href="https://github.com/jonas52/systek"><img src="https://img.shields.io/badge/repo-github-black?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="https://github.com/jonas52/systek/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-project-blue?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/platform-linux-2ea44f?style=for-the-badge&logo=linux" alt="Linux">
  <img src="https://img.shields.io/badge/interface-terminal-1f6feb?style=for-the-badge" alt="Terminal">
</p>

</div>

---

## Preview

<div align="center">
  <img src="./assets/screenshot.png" alt="Systek preview" width="900">
</div>

---

## Overview

Systek is a Linux terminal administration menu designed to group common server actions into a single, clean interface.

It helps you run daily administration tasks faster, reduces command typing mistakes, and gives you quick access to the most useful system operations from one place.

---

## Features

<table>
  <tr>
    <td valign="top" width="50%">

### System administration

* Update the system
* Reboot the server
* Power off the server
* Check host and IP address
* Monitor CPU, RAM, and disk usage
* Check CPU temperature

### Services

* Restart a service
* Enable a service
* Disable a service
* List services
* Monitor a service
* View live logs
* Backup server logs

    </td>
    <td valign="top" width="50%">

### Network and security

* Check network connections
* Show UFW status
* Enable the firewall
* Disable the firewall
* Add firewall rules
* Remove firewall rules

### Storage and packages

* Check disk space
* Mount a drive
* List connected disks
* Install a package
* Remove a package
* Hold or unhold a package

    </td>
  </tr>

</table>

### Built-in Systek actions

* Update Systek
* Remove Systek
* Enable autostart at session login
* Disable autostart
* Install Cockpit

---

## Installation

> The current `install.sh` is meant to run with the repository files available locally, because it copies `systek.py` and `README.md` into `/opt/systek`.

### One-line installer

```bash
git clone https://github.com/jonas52/systek.git && cd systek && sudo bash install.sh
```

### Temporary install without keeping the repo

```bash
tmpdir=$(mktemp -d) && git clone https://github.com/jonas52/systek.git "$tmpdir/systek" && cd "$tmpdir/systek" && sudo bash install.sh
```

---

## Usage

```bash
sudo systek
```

### Update

```bash
sudo systek --update
```

### Remove

```bash
sudo systek --remove
```

---

## Autostart

Systek includes an autostart option that makes the script launch automatically when the user session starts.

When autostart is enabled, Systek creates a startup entry so the application runs at login without needing to launch it manually. This is useful if you want the administration menu to open automatically on a local machine, admin workstation, or dedicated environment.

In practice, this means:

* the script starts at the beginning of the session
* you do not need to run `sudo systek` manually every time
* it is mainly useful for environments where you want immediate access to the menu after login

Autostart can be disabled at any time from the menu.

---

## Requirements

* Linux
* Python 3
* Git
* Root or sudo privileges
* Dependencies installed automatically depending on the distribution

---

## Project structure

```text
.
├── install.sh
├── systek.py
├── README.md
└── LICENSE
```

---

## Notes

* Installation creates a symbolic link in `/usr/local/bin/systek`
* The application should be run with administrator privileges
* The update command depends on the way the project was installed

---

## License

Distributed under the terms defined in the `LICENSE` file.

---

<div align="center">
  <sub>Built to simplify Linux administration from the terminal.</sub>
</div>

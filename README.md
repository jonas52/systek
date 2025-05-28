<h1 align="center">Systek 🛠️</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/723bcab7-30a6-47a6-873b-cc3ffc44d226" alt="Script Preview" width="300">
</p>

<p align="center"><strong>A versatile Python-based CLI tool to manage your Linux server with ease.</strong></p>

<p align="center"><em>⚠️ Please note: This project is currently under development and is only supported on Ubuntu at this time.</em></p>

---

## ✨ Features

* ✅ Clean, interactive terminal interface
* 🔁 Manage system services (start, stop, restart, enable, disable)
* 📦 Install and remove packages
* 📊 Monitor system resources (CPU, RAM, disk, network)
* 🌡️ Display CPU temperature (requires `lm-sensors`)
* 🔒 Manage UFW firewall settings
* 🖥️ Install the Cockpit web admin interface
* 🔄 Self-update the script using `--update`
* 🧹 Uninstall Systek and clean up with `--remove`

---

## 📋 Requirements

Before installing Systek, ensure the following:

* **Python 3.x** is installed
* **Root or sudo privileges** are available
* *(Optional)* For CPU temperature support:

  ```bash
  sudo apt-get install lm-sensors
  ```

---

## 🚀 Installation

### 📦 One-liner (install & run):

```bash
bash <(curl -s https://raw.githubusercontent.com/jonas52/systek/main/install_service.sh) && systek
```

### 📦 One-liner (install only):

```bash
bash <(curl -s https://raw.githubusercontent.com/jonas52/systek/main/install_service.sh)
```

This script will:

* Clone the repository into `/opt/systek`
* Set up a systemd service
* Make the `systek` command globally available

---

## 🧑‍💻 Usage

### ▶️ Launch the interactive menu:

```bash
systek
```

### 🔄 Update Systek:

```bash
systek --update
```

### ❌ Uninstall Systek:

```bash
systek --remove
```

---

## 📝 License

This project is licensed under the [GNU General Public License v2.0](LICENSE).

---

<p align="center"><strong>Made with ❤️ by jonas52</strong></p>

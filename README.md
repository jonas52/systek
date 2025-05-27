<h1 align="center">Systek 🛠️</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/723bcab7-30a6-47a6-873b-cc3ffc44d226" alt="Script Preview" width="300">
</p>

<p align="center"><strong>A powerful Python script to manage your Linux server from the terminal.</strong></p>

---

## ✨ Features

- ✅ Simple and interactive terminal menu
- 🔁 System and service management (start, stop, restart, enable, disable)
- 📦 Package installation/removal
- 📊 Resource monitoring (CPU, RAM, Disk, Network)
- 🌡️ CPU temperature display (requires `lm-sensors`)
- 🔒 UFW firewall management
- 🖥️ Cockpit web admin installation
- 🔄 Git auto-update via `--update`
- 🧹 Service and script removal via `--remove`

---

## 📋 Prerequisites

Before using Systek, make sure you have:

- **Python 3.x** installed
- **sudo/root privileges**
- *(Optional)* For CPU temperature:  
  ```bash
  sudo apt-get install lm-sensors
  ```

---

## 🚀 Installation

### 📦 One-liner launch

```bash
bash <(curl -s https://raw.githubusercontent.com/jonas52/systek/main/install_service.sh) | systek
```

### 📦 One-liner install 

```bash
bash <(curl -s https://raw.githubusercontent.com/jonas52/systek/main/install_service.sh)
```

This command will:
- Clone the repo into `/opt/systek`
- Set up the systemd service
- Make the `systek` command globally available

---

## 🧑‍💻 Usage

### 📜 Run the menu:

```bash
systek
```

### 🔄 Update the script:

```bash
systek --update
```

### ❌ Remove the service and the script:

```bash
systek --remove
```

---

## 📝 License

This project is licensed under the [GNU General Public License v2.0](LICENSE).

---

<p align="center"><strong>Made with ❤️ by jonas52</strong></p>

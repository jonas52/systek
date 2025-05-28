#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "╰─╼ This script must be run as superuser (root)."
    exit 1
fi

# Detect package manager
if command -v apt > /dev/null 2>&1 ; then
    PKG_MANAGER="apt"
    INSTALL_CMD="apt update && apt install -y"
elif command -v dnf > /dev/null 2>&1 ; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="dnf install -y"
elif command -v yum > /dev/null 2>&1 ; then
    PKG_MANAGER="yum"
    INSTALL_CMD="yum install -y"
elif command -v pacman > /dev/null 2>&1 ; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="pacman -Sy --noconfirm"
else
    echo "╰─╼ Unsupported package manager. Install Git manually and rerun the script."
    exit 1
fi

# Install git if not present
if ! command -v git > /dev/null 2>&1; then
    echo "│ Git not found. Installing with $PKG_MANAGER..."
    eval "sudo $INSTALL_CMD git > /dev/null 2>&1"
    if [ $? -ne 0 ]; then
        echo "╰─╼ Failed to install git. Aborting."
        exit 1
    fi
fi

# Ensure Python ≥ 3.10 is available
PYTHON_OK=false
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    VERSION_OK=$(echo "$PYTHON_VERSION >= 3.10" | bc)
    if [ "$VERSION_OK" -eq 1 ]; then
        PYTHON_OK=true
    fi
fi

if [ "$PYTHON_OK" != true ]; then
    echo "│ Python >= 3.10 not found. Installing Python 3.12 with $PKG_MANAGER..."

    case $PKG_MANAGER in
        apt)
            add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
            apt update -y > /dev/null 2>&1
            apt install -y python3.12 > /dev/null 2>&1
            ;;
        dnf|yum)
            $PKG_MANAGER install -y python3.12 > /dev/null 2>&1
            ;;
        pacman)
            pacman -Sy --noconfirm python312 > /dev/null 2>&1
            ;;
    esac

    if ! command -v python3.12 &>/dev/null; then
        echo "╰─╼ Python 3.12 installation failed."
        exit 1
    fi
    ln -sf "$(command -v python3.12)" /usr/bin/python3
    echo "│ Python 3.12 installed and set as default python3."
fi

# Install pip if missing
if ! command -v pip3 &>/dev/null; then
    echo "│ pip3 not found. Installing with $PKG_MANAGER..."
    case $PKG_MANAGER in
        apt)
            apt install -y python3-pip > /dev/null 2>&1
            ;;
        dnf|yum)
            $PKG_MANAGER install -y python3-pip > /dev/null 2>&1
            ;;
        pacman)
            pacman -Sy --noconfirm python-pip > /dev/null 2>&1
            ;;
    esac
fi

# Install netifaces module
echo "│ Installing Python module: netifaces"
pip3 install netifaces > /dev/null 2>&1


REPO_URL="https://github.com/jonas52/systek.git"
INSTALL_DIR="/opt/systek"
SERVICE_NAME="systek"
ENTRY_POINT="systek.py"
SYMLINK_PATH="/usr/local/bin/systek"

# Clone or update repo
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "│ Updating existing repo..."
    git -C "$INSTALL_DIR" pull > /dev/null 2>&1
else
    echo "│ Cloning repo to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR" > /dev/null 2>&1
fi

# Make sure script is executable
chmod +x "$INSTALL_DIR/$ENTRY_POINT" > /dev/null 2>&1

# Create systemd service
echo "│ Creating systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null
[Unit]
Description=Systek Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/$ENTRY_POINT
WorkingDirectory=$INSTALL_DIR
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload > /dev/null 2>&1
sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
sudo systemctl restart "$SERVICE_NAME" > /dev/null 2>&1

# Create symlink
echo "│ Creating symlink: $SYMLINK_PATH"
sudo ln -sf "$INSTALL_DIR/$ENTRY_POINT" "$SYMLINK_PATH" > /dev/null 2>&1

echo "╰─╼ Installation complete. Use 'systek', 'systek --update' or 'systek --remove'."
